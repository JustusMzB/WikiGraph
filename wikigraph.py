import wikiarticle
from time import time
from pyvis.network import Network
import requests
import networkx as nx
from wikigraph_misc import debug_timing

class WikiNode:
    """Representation of a Node within a graph of referencing wikipedia articles
    """
    def __init__(self, article, depth, session = None) -> None:
        """Initializes a wikipedia node

        Args:
            article (str | WikiArticle): The url to a wikpedia article, or an WikiArticle object wrapping one
            depth (int): Depth in which the node is located within the Graph.
            session (requests.Session, optional): Session for the wrapped WikiArticle object to be created with. Defaults to None, creating a new session.

        Raises:
            TypeError: The wikiarticle parameter is no url or WikiArticle object.
        """
        if type(article) == str: #Can init with url
            self.article = wikiarticle.WikiArticle(article, session=session)
        elif type(article) == wikiarticle.WikiArticle:
            self.article = article
        else:
            raise TypeError('Can only initialize with url or WikiArticle object.')
        self._outgoing = set()
        self._incoming = set()
        # Consideration: Add field of the graph itself to allow node-function of gathering adjacencies
        # For now, adjacencies need to be added externally.

        self.depth = depth

    def add_outgoing_reference(self, referenced_node):
        """Adds a directed edge from the node to another, ensuring that the other node is aware of this new incoming edge.

        Args:
            referenced_node (WikiNode): The node to which the edge should be directed.
        """ 
        self._outgoing.add(referenced_node)
        referenced_node._incoming.add(self)
    
    def add_incoming_reference(self, referencing_node):
        """Adds a directed edge from another node to this one, ensuring that the other node is aware of this new outgoing edge.

        Args:
            referencing_node (WikiNode): The node from which the edge should be incoming.
        """
        self._incoming.add(referencing_node)
        referencing_node._outgoing.add(self)

    @property
    def out_degree(self):
        """The amount of directed edges going away from this node

        Returns:
            int: out degree of the node
        """                 
        return len(self._outgoing)

    @property
    def in_degree(self):
        """The amount of directed edges coming towards this node

        Returns:
            int: in degree of the node
        """                 
        return len(self._incoming)

    #These are returning tuple versions to prevent editing of the set.
    @property
    def referencing_nodes(self):
        """
        Returns:
            referenced nodes: nodes that are connected to this one by outgoing edges
        """
        return tuple(self._incoming)

    @property
    def referenced_nodes(self):
        """
        Returns:
            referencing nodes: nodes that are connected to this one by incoming edges
        """
        return tuple(self._outgoing)
    def __str__(self) -> str:
        return f'< WikiNode Object wrapping article {self.article} > '

class WikiGraph:
    """Graph representation of a wikipedia article and its surrounding references
    """
    def __init__(self, root, depth=10, max_nodes=500) -> None:
        """

        Args:
            root (url | WikiNode): Article around which the graph should be constructed.
            depth (int, optional): Maximum amount of references across which an article added to the graph may be away from the root. Defaults to 10.
            max_nodes (int, optional): Maximum amount of nodes that the graph is allowed to contain. Defaults to 500.

        Raises:
            TypeError: root parameter is not a string and therefore no url, or no Wiki
        """
        #The session prevents unneccessary Handshakes, thus reducing the time
        #To download hundreds to thousands of Wikipedia-Pages by a factor of around 2
        self._getter_session = requests.Session()

        self._max_nodes = max_nodes
        if type(root) == str:
            self.root = WikiNode(root, depth=0, session = self._getter_session)
        elif type(root) == WikiNode:
            self.root = root
        elif type(root) == wikiarticle.WikiArticle:
            self.root = WikiNode(root, 0, self._getter_session)
        else:
            raise TypeError('Can only initialize Graph with root node or url.')

        self.nodes : dict[str, WikiNode] = {}
        self.nodes[self.root.article.url] = self.root
        self.width_first_completion(depth)

    def _add_node(self, url, parent: WikiNode):
        """Adds a node to the graph.

        Args:
            url (str): url of the new article to be added
            parent (WikiNode): Node with Article that referenced this one
        Returns:
            boolean: Was the node already Present, and only references needed to be updated?
        """
        if url not in self.nodes.keys():
            # slightly more resistant against bad WikiNode implementations
            # with bad equals implementation
            new_Node = WikiNode(url, parent.depth+1, self._getter_session)
            parent.add_outgoing_reference(new_Node)
            self.nodes[url] = new_Node
            return False
        else:
            parent.add_outgoing_reference(self.nodes[url])
            return True

    def add_referenced(self, node: WikiNode):
        """Overflow-safe attempt of adding all articles to the graph, which are referenced by one article

        Args:
            node (WikiNode): Source of the references
        """
        if node not in self.nodes.values():
            raise ValueError("Only References of Articles within the graph may be added!")
        size = len(self.nodes)
        added_nodes = 0
        for reference in node.article.references:
            if not self._add_node(reference, node):
                size += 1
                added_nodes += 1
            if size >= self._max_nodes: return added_nodes
        return added_nodes

    @debug_timing
    def width_first_completion(self, depth: int):
        """Width-First approach to constructing the graph. All references from within one depth will be added before proceeding
        to the next depth.

        Args:
            depth (int): depth up to which references will be added to the graph

        Returns:
            int: Number of nodes that were added in this step.
        """
        size = len(self.nodes)
        start_size = size
        start_time = time()
        print(f'Completing Graph to a depth of up to {depth} or a maximum of {self._max_nodes} wikinodes...')
        total_added_nodes = 0
        completed_nodes = 0
        avg_treatment_time = 0
        avg_additions = 0
        for i in range(depth):
            # Workaround: The nodes that will be added per round are not relevant, so decouple iteration from graph.
            # Otherwise we will receive a 'Dict changed Size' runtime error.
            to_be_completed_this_round = list(filter(lambda node: node.depth == i, self.nodes.values()))
            layer_start = time()

            for node in to_be_completed_this_round:
                    node_start = time()
                    added_nodes = self.add_referenced(node)
                    total_added_nodes += added_nodes
                    node_done = time() - node_start
                    completed_nodes += 1

                    # Update of progress.
                    # Calculation per treated node averages
                    avg_treatment_time = ((completed_nodes -1) * avg_treatment_time + node_done)/completed_nodes
                    avg_additions = ((completed_nodes -1 ) * avg_additions + added_nodes ) /completed_nodes
                    # Time until all layers would be completed
                    eta_layer_limit = (avg_additions ** (depth)) * avg_treatment_time
                    # Time until maximum nodes are reached (with estimate of single node creation time)
                    eta_node_limit = (avg_treatment_time / avg_additions) * (self._max_nodes - start_size)
                    # Output of estimated waiting time. ETA only grows somewhat reliable for very large graphs...
                    print(f'Treating level {i}; total to be treated:{len(to_be_completed_this_round)}; Finished treatment for: {completed_nodes}.; nodes added:{total_added_nodes}; Estimated remaining time: {min(eta_layer_limit, eta_node_limit) - (time() - start_time):.2f}s', end='\r')
                    size = len(self.nodes)
                    if size>= self._max_nodes:
                        break
            layer_time = time() - layer_start
            if size >= self._max_nodes:
                break
        print("\nCompleted.") # Terminating the self overriding progress line
    @property
    def node_with_max_out_degree(self):
        """
        Returns:
            WikiNode: Node with the most outgoing references aka. highest out degree
        """
        return max(self.nodes.values(), key=lambda node: node.out_degree)

    @property
    def node_with_max_in_degree(self):
        """
        Returns:
            WikiNode: Node with the most incoming references aka. highest in degree
        """
        return max(self.nodes.values(), key=lambda node: node.in_degree)

    def _count_edges(self):
        """
        Returns:
            int: amount of edges within the graph
        """
        counter = 0
        for i in self.nodes.values():
            counter += len(i.referenced_nodes)
        return counter
    @property
    def density(self):
        """

        Returns:
            float: density of the graph, simply speaking: 
            How close is the graph to having the maximum amount of edges possible for its amount of nodes.
        """
        return self._count_edges() / (len(self.nodes) * (len(self.nodes) -1))

    def save(self, path=None):
        """Saves the wikigraph to a pickle file.

        Args:
            path (str, optional): Path under which the file should be stored. Defaults to . Defaults to ./{root-title}-Wikigraph.pickle

        Raises:
            FileNotFoundError: the path does not exist.
            FileExistsError: there is already a file in this path. No overwriting.
        """
        if path == None:
            path = f'./{self.root.article.title}-Wikigraph.pickle'
            path.replace(' ', '_')
        
        try:
            file = open(path, mode='xb')
            pickle.dump(self, file)
            file.close()
        except FileNotFoundError:
            errormessage = f'The path {path} does appearently not point to a file.'
            logging.error(errormessage)
            raise FileNotFoundError(errormessage)
        except FileExistsError:
            errormessage=f'{path} points to an existing file. We are not overwriting!'
            logging.error(errormessage)
            raise FileExistsError(errormessage)
    @staticmethod
    def load(path):
        """Loads a wikigraph from a file

        Args:
            path (str): Path to the file in which the Wikigraph is stored

        Raises:
            TypeError: The file existed, but does not hold a wikigraph.

        Returns:
            WikiGraph: wikigraph that was stored inside the file.
        """
        with open(path, mode='rb') as file:
            wikigraph: WikiGraph =  pickle.load(file) # Should secure that this is a wikigraph we are loading.
            if not isinstance(wikigraph, WikiGraph):
                raise TypeError(f'{path} does not point to a WikiGraph-File!')
            return wikigraph
            

    @debug_timing
    def draw(self, search_term:str=None, search_html:bool=False, height:int=1000, width:int=800):
        """Creates an html file with a visualization of the graph, and opens it in the standard browser.

        Args:
            search_term (str, optional): If set, all nodes containing the search term will be highlighted in the graph depiction. Defaults to None.
            search_html (bool, optional): If set, html will be searched for the search term.
            height (int, optional): Height of the graph depiction in px. Defaults to 1000
            width(int, optional): Width of the graph depiction in px. Defaults to 800
        """
        network = Network(directed=True, height=f'{height}px', width=f'{width}px')
        for node_key in self.nodes:
            article = self.nodes[node_key].article
            found_search=False
            if search_term:
                found_search = search_term in article.title
                # Only look in HTML if required, and if title did not yield result.
                if not found_search and search_html:
                    found_search = search_term in article.html
            if found_search:
                network.add_node(node_key, label=article.title, color="red")
            else:
                network.add_node(node_key, label=article.title)
        for node_key in self.nodes.values():
            for referenced in node_key.referenced_nodes:
                network.add_edge(node_key.article.url, referenced.article.url)
        network.force_atlas_2based()
        network.show_buttons(filter_=["physics"])
        network.show(name=f'{self.root.article.title.replace(" ", "_")}_graph.html')

    @debug_timing
    def write_to_gml(self, path, with_html=False):
        """Writes the Graph into the gml format. This allows for better investigation options in interactive
        graph-exploration software.

        Args:
            path (str): path to the wished for file location
            with_html (bool, optional): If True, the html is added as a property to each node. Massively increases size. Defaults to False.
        """
        digraph = nx.DiGraph()
        # Add nodes first, with title-Property and possibly html
        if with_html:
            for node in self.nodes.values():
                digraph.add_node(node.article.url, title=node.article.title, html=node.article.html)
        else:
            for node in self.nodes.values():
                digraph.add_node(node.article.url, title=node.article.title)
        # Add all edges
        for node in self.nodes.values():
            for target_node in node.referenced_nodes:
                digraph.add_node(node.article.url, target_node.article.url)
     
        nx.write_gml(G=digraph, path=path)
      
    def __str__(self) -> str:
        return f'<WikiGraph Object with {len(self.nodes)} nodes: root = {self.root}>'

###
# If the Module is executed, a graph around the wiki page of JK Rowling is created.
###
if __name__ == '__main__':
    graph = WikiGraph("https://de.wikipedia.org/wiki/Joanne_K._Rowling")

    