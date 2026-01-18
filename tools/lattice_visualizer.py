import matplotlib.pyplot as plt
import networkx as nx

# Ultramasterism Lattice Graph
G = nx.DiGraph()
G.add_node("Tutoring Core", level=3)
G.add_node("Mirror Core (PvP/ZvZ/TvT)", level=2)
G.add_node("Cross Webbing (All Matchups)", level=1)
G.add_node("Absolute Pure Truth Apex", level=0)

G.add_edges_from([
    ("Tutoring Core", "Mirror Core (PvP/ZvZ/TvT)"),
    ("Mirror Core (PvP/ZvZ/TvT)", "Cross Webbing (All Matchups)"),
    ("Cross Webbing (All Matchups)", "Absolute Pure Truth Apex")
])

pos = nx.multipartite_layout(G, subset_key="level")
nx.draw(G, pos, with_labels=True, node_color="powrush_blue", font_weight="bold", arrows=True)
plt.title("SC2-Ultramasterism Lattice")
plt.show()
