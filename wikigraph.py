import wikiarticle
from time import time
from pyvis.network import Network
import requests

from wikigraph_misc import debug_timing

class WikiNode:
    def __init__(self, article: wikiarticle.WikiArticle, depth = None, session = None) -> None:
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
        self._outgoing.add(referenced_node)
        referenced_node._incoming.add(self)
    
    def add_referencing(self, referencing_node):
        self._incoming.add(referencing_node)
        referencing_node._outgoing.add(self)

    @property
    def out_degree(self):
        return len(self._outgoing)

    @property
    def in_degree(self):
        return len(self._incoming)

    #These are returning tuple versions to prevent editing of the set.
    @property
    def referencing_nodes(self):
        return tuple(self._incoming)

    @property
    def referenced_nodes(self):
        return tuple(self._outgoing)


class WikiGraph:
    def __init__(self, root, depth=10, max_nodes=500) -> None:
        #The session prevents unneccessary Handshakes, thus reducing the time
        #To download hundreds to thousands of Wikipedia-Pages by a factor of around 2
        self.getter_session = requests.Session()

        self.max_nodes = max_nodes
        if type(root) == str:
            self.root = WikiNode(root, depth=0, session = self.getter_session)
        elif type(root) == WikiNode:
            self.root = root
        else:
            raise TypeError('Can only initialize Graph with root node or url.')

        self.nodes : dict[str, WikiNode] = {}
        self.nodes[self.root.article.url] = self.root
        self.complete_to_depth(depth)

    def add_node(self, url, parent: WikiNode):
        if url not in self.nodes.keys():
            new_Node = WikiNode(url, parent.depth+1, self.getter_session)
            parent.add_reference(new_Node)
            self.nodes[url] = new_Node
        else:
            parent.add_reference(self.nodes[url])

    def add_referenced(self, node: WikiNode):
        size = len(self.nodes)
        for reference in node.article.references:
            self.add_node(reference, node)
            size += 1
            if size >= self.max_nodes: return

    @debug_timing
    def complete_to_depth(self, depth: int):
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
        return max(self.nodes.keys(), key=lambda node: node.out_degree)

    @property
    def with_max_in_degree(self):
        return max(self.nodes.keys(), key=lambda node: node.in_degree)

    def _count_edges(self):
        counter = 0
        for i in self.nodes.keys():
            counter += len(i.referenced_nodes)
        return counter

    def graph_density(self):
        return self._count_edges() / (len(self.nodes) * (len(self.nodes) -1))

    @debug_timing
    def draw(self):
        network = Network(directed=True)
        for node in self.nodes:
            network.add_node(node, label=self.nodes[node].article.title)
        for node in self.nodes.values():
            for referenced in node.referenced_nodes:
                network.add_edge(node.article.url, referenced.article.url)
        network.show_buttons()
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
if __name__ == '__main__':
    graph = WikiGraph("https://de.wikipedia.org/wiki/Joanne_K._Rowling", depth=2)

    