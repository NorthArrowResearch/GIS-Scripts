import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import timeit
from shapely.geometry import *

t0 = timeit.timeit()

def timed(msg):
    t1 = timeit.timeit()
    print msg + " " + str(t0 - t1)

# https://networkx.github.io/documentation/development/reference/algorithms.html
def findnodewithID(id):
    return next(iter([e for e in G.edges_iter() if G.get_edge_data(*e)['OBJECTID'] == id]), None)

timed("started")

# Load a shape file:
G = nx.read_shp('data/NHDFlowline_Minam_clean.shp', simplify=False)
pos = {v: v for k, v in enumerate(G.nodes())}
timed("loaded and parsed")

# Get all edges with IsHeadWate == 1
headwateredges = [e for e in G.edges_iter() if G.get_edge_data(*e)['IsHeadwate'] == 1]

startid = 2492
endid = 3850
start = findnodewithID(2492)
end = findnodewithID(3850)

GG = G.to_undirected()

# Make a depth-first tree from the first headwater we find
path = nx.shortest_path(GG, source=start[0], target=end[0])
path_edges = zip(path, path[1:])


# Now let's print some stuff out about this and draw some prettgot add y graphs


# We'll create a line from this path and measure the length of it.
ls = LineString(path)

ax = plt.axes()
ax.set_aspect(1)


# place a text box in upper left in axes coords
textstr = 'Edges: {0}\nNodes: {1}\nStartID: {2}\nEndID {3}\nPathDist: {4}'.format(len(G.nodes()), len(G.edges()), startid, endid, ls.length)
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
        verticalalignment='top', bbox=props)

nx.draw_networkx_edges(GG, pos, ax=ax, edge_color='black', width=1)
nx.draw_networkx_edges(GG,pos, ax=ax, edgelist=path_edges, edge_color='red', width=3)
timed("drawn")


plt.show()
timed("done")