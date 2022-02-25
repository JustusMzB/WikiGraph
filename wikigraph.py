import wikiarticle
from time import time
from pyvis.network import Network
import requests

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

    def add_reference(self, referenced_node):
        """Adds a directed edge from the node to another, ensuring that the other node is aware of this new incoming edge.

        Args:
            referenced_node (WikiNode): The node to which the edge should be directed.
        """ 
        self._outgoing.add(referenced_node)
        referenced_node._incoming.add(self)
    
    def add_referencing(self, referencing_node):
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

        self.max_nodes = max_nodes
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
        self.complete_to_depth(depth)

    def _add_node(self, url, parent: WikiNode):
        """Adds a node to the graph.

        Args:
            url (str): url of the new article to be added
            parent (WikiNode): Node with Article that referenced this one
        """
        if url not in self.nodes.keys():
            # slightly more resistant against bad WikiNode implementations
            # with bad equals implementation
            new_Node = WikiNode(url, parent.depth+1, self._getter_session)
            parent.add_reference(new_Node)
            self.nodes[url] = new_Node
        else:
            parent.add_reference(self.nodes[url])

    def add_referenced(self, node: WikiNode):
        """Overflow-safe attempt of adding all articles to the graph, which are referenced by one article

        Args:
            node (WikiNode): Source of the references
        """
        if node not in self.nodes.values():
            raise ValueError("Only References of Articles within the graph may be added!")
        size = len(self.nodes)
        for reference in node.article.references:
            self._add_node(reference, node)
            size += 1
            if size >= self.max_nodes: return

    @debug_timing
    def complete_to_depth(self, depth: int):
        """Width-First approach to constructing the graph. All references from within one depth will be added before proceeding
        to the next depth.

        Args:
            depth (int): depth up to which references will be added to the graph
        """
        size = len(self.nodes)
        for i in range(depth):
            # Workaround: The nodes that will be added per round are not relevant, so decouple iteration from graph.
            # Otherwise we will receive a 'Dict changed Size' runtime error.
            to_be_completed_this_round = list(filter(lambda node: node.depth == i, self.nodes.values()))
            start = time()
            for node in to_be_completed_this_round:
                    self.add_referenced(node)
                    size = len(self.nodes)
                    if size>= self.max_nodes:
                        break
            ex_time = time() - start
            if size >= self.max_nodes:
                break
            print(f'took {ex_time}s to complete adding referenced articles from {len(to_be_completed_this_round)} articles.')
    @property
    def with_max_out_degree(self):
        """
        Returns:
            WikiNode: Node with the most outgoing references aka. highest out degree
        """
        return max(self.nodes.keys(), key=lambda node: node.out_degree)

    @property
    def with_max_in_degree(self):
        """
        Returns:
            WikiNode: Node with the most incoming references aka. highest in degree
        """
        return max(self.nodes.keys(), key=lambda node: node.in_degree)

    def _count_edges(self):
        """
        Returns:
            int: amount of edges within the graph
        """
        counter = 0
        for i in self.nodes.keys():
            counter += len(i.referenced_nodes)
        return counter

    def graph_density(self):
        """

        Returns:
            float: density of the graph, simply speaking: 
            How close is the graph to having the maximum amount of edges possible for its amount of nodes.
        """
        return self._count_edges() / (len(self.nodes) * (len(self.nodes) -1))

    @debug_timing
    def draw(self):
        """Creates an html file with a visualization of the graph, and opens it in the standard browser.
        """
        network = Network(directed=True)
        for node in self.nodes:
            network.add_node(node, label=self.nodes[node].article.title)
        for node in self.nodes.values():
            for referenced in node.referenced_nodes:
                network.add_edge(node.article.url, referenced.article.url)
        network.show_buttons()
        ### Standard options exported from configureable view.
        network.set_options('''"var options = {
  "edges": {
    "color": {
      "inherit": true
    },
    "smooth": false
  },
  "layout": {
    "hierarchical": {
      "enabled": true
    }
  },
  "interaction": {
    "hideEdgesOnDrag": true
  },
  "physics": {
    "hierarchicalRepulsion": {
      "centralGravity": 0
    },
    "minVelocity": 0.75,
    "solver": "hierarchicalRepulsion"
  }
}''')
        network.show(name=f'{self.root.article.title.replace(" ", "_")}_graph.html')


###
# If the Module is executed, a graph around the wiki page of JK Rowling is created.
###
if __name__ == '__main__':
    graph = WikiGraph("https://de.wikipedia.org/wiki/Joanne_K._Rowling")

    