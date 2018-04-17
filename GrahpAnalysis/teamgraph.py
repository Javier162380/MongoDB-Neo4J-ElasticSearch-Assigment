import networkx as nx
import matplotlib.pyplot as plt
import toolz
import json
from itertools import chain

with open('nflresults.json', 'r',errors='ignore') as nfl:
    results = json.load(nfl)

teams=list(chain.from_iterable(results))
teams_hash=toolz.groupby('team', teams)
results=[]
for key, team in teams_hash.items():
    team_name = key
    college_unique=set()
    for college in team:
        if college['college'] not in college_unique:
            results.append(tuple([team_name,college['college']]))
        else:
            college_unique.add(college['college'])


Graph = nx.Graph()
Graph.add_edges_from(results, color='red')
pos = nx.spring_layout(Graph)
### edges
nx.draw_networkx_edges(Graph,pos, alpha=0.4,width=1,edge_color='red',cmap='blue')
nx.draw_networkx_nodes(Graph, pos,node_size=40,
                       cmap='blue')

# labels
nx.draw_networkx_labels(Graph,pos,font_size=8, font_family='sans-serif')
plt.axis('on')
plt.savefig("weighted_graph.png")  # save as png
plt.show()  # display