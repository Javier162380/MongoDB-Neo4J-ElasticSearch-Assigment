import networkx as nx
import toolz
import json
from itertools import chain
from pandas import DataFrame
from operator import itemgetter
from bokeh.io import show, output_file
from bokeh.plotting import figure
from bokeh.models.graphs import from_networkx,NodesAndLinkedEdges,EdgesAndLinkedNodes
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool, TapTool, BoxSelectTool,ColumnDataSource
from bokeh.palettes import Spectral4



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


NFLGraph = nx.Graph()
NFLGraph.add_edges_from(results, color='red')
#we caculate the degree of centrality, depending of .
node_size={entity:size*80 for entity,size in  nx.degree_centrality(G=NFLGraph).items()}
node_color={}
teams = ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND',
             'JAC', 'KC', 'LA', 'MIA', 'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'OAK', 'PHI', 'PIT', 'SD', 'SEA', 'SF', 'TB',
             'WAS']
for entity , size in node_size.items():
    #if that happen we have a team.
    if entity in teams:
        node_color.update({entity:Spectral4[0]})
    else:
        node_color.update({entity:Spectral4[3]})

### set node attributes
nx.set_node_attributes(NFLGraph, 'node_size', node_size)
nx.set_node_attributes(NFLGraph, 'node_color', node_color)
#we reference the edges
source = ColumnDataSource(DataFrame.from_dict({k:v for k,v in NFLGraph.nodes(data=True)},orient='index'))

#we create the plot
plot = Plot(plot_width=1250, plot_height=900,
            x_range=Range1d(-1.1,1.1), y_range=Range1d(-1.1,1.1))
plot.title.text = "NFL Colleges-Teams Relation"
plot.add_tools(HoverTool(tooltips=None), TapTool(), BoxSelectTool())
graph = from_networkx(NFLGraph, nx.spring_layout, scale=2, center=(0,0))
graph.node_renderer.data_source = source
graph.node_renderer.glyph = Circle(size='node_size',fill_color = 'node_color')
graph.node_renderer.selection_glyph = Circle(size='node_size',fill_color = 'node_color')
graph.node_renderer.hover_glyph = Circle(size='node_size', fill_color = 'node_color')
graph.edge_renderer.hover_glyph = MultiLine(line_color=Spectral4[2], line_width=1)
graph.edge_renderer.glyph = MultiLine(line_color="#CCCCCC", line_alpha=2, line_width=1)
graph.selection_policy = NodesAndLinkedEdges()
graph.inspection_policy = EdgesAndLinkedNodes()
plot.renderers.append(graph)
output_file("NFL-teams-colleges.html")
show(plot)