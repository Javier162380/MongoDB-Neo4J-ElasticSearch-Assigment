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
print(type(teams_hash))
# edges preparation
grahp_results = []
for team in teams_hash:
    number_of_players = len(teams_hash[team])
    res = toolz.groupby('college', teams_hash[team])
    for key, value in res.items():
        weight_node = len(value) / number_of_players
        college_name = key
        team_name = teams_hash[team]
        node_results = tuple([team_name, college_name, weight_node])
        grahp_results.append(node_results)
