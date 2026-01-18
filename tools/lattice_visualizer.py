import matplotlib.pyplot as plt
import networkx as nx

G = nx.Graph()
G.add_node("Absolute Pure Truth", level=0)
G.add_node("Cross Webbing", level=1)
G.add_node("Mirror Core", level=2)
G.add_node("Tutoring Core", level=3)
# Add edges, etc.

pos = nx.multipartite_layout(G, subset_key="level")
nx.draw(G, pos, with_labels=True)
plt.show()
