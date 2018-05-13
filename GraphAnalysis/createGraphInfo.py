from bson import ObjectId
import networkx as nx
import toolz
import json
from itertools import chain
import time
from bs4 import BeautifulSoup
import urllib
from urllib.request import Request
import collections


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


"""
Dumps the content from "dic" to the path of "json_path"
"""
def create_output_file(json_path, dic):
    with open(json_path, 'w') as outfile:
        json.dump(dic, outfile, cls=JSONEncoder, indent=4)


"""
    Returns a list with all the tuples corresponding to the edges of the graph
    ( tupple  -> (source node,target node) of each edge)
"""
def create_graph_connections(results, occurrences):
    teams = list(chain.from_iterable(results))

    teams_hash = toolz.groupby('team', teams)
    graph_results = []

    # As we group by team, we iterate over all edges whose targets side belongs to that team
    for key, team in teams_hash.items():
        team_name = key

        # we store the number of colleges belonging to each team
        occurrences[team_name]=len(team)
        college_unique = set()

        # if the edge has already been added, we do not include again the edge as a tuple
        for college in team:
            if college['college'] not in college_unique:
                graph_results.append(tuple([team_name, college['college']]))
            else:
                college_unique.add(college['college'])

    # we return the edges
    return graph_results

"""
Creates a graph from the variable "graph_results" provided
"""
def create_graph(graph_results):
    NFLGraph = nx.Graph()
    NFLGraph.add_edges_from(graph_results)
    print(nx.info(NFLGraph))
    return NFLGraph


"""
Creates the information of each node 
"""
def create_node_with_info(node, occurrences, betweenness, closeness, url_of_all_teams,  count_players_each_college):
    node_dict = {}
    node_dict["id"] = node
    try:
        node_dict ["players_received"] = occurrences[node]
        node_dict["type"] = "team"

        """
        Taking a look to the code of "https://www.nfl.com/teams", we realized that all images came in the format
        of the line below 
        """
        node_dict["image"] = 'https://static.nfl.com/static/site/img/logos/svg/teams/{0}.svg'.format(node)
    except KeyError:

        "if node_dict [players_received] = occurrences[node] throws an error, we have a node of a college"
        node_dict["players_received"] = 0
        node_dict["type"] = "college"
        node_dict["players_provided"] = count_players_each_college[node]
        pass
    node_dict["betweenness"] = betweenness[node]
    node_dict["closeness"] = closeness[node]
    set_url_of_a_team(node_dict, url_of_all_teams)
    return node_dict

"""
Returns all teams with their corresponding ESPN site
"""
def get_all_url_of_all_teams():
    dict_all_teams_abbr = {}

    """
    We scrape the first site: 
    The first one is to get the correspondence between each team abbreviation and its name 
    (since the API give us just the abbreviation.)
     
    -----------------------------------
    |   TeamID	  |     City & Name   |
    |----------------------------------
    |   ARI	      |     Arizona       |
    |----------------------------------
    
    """
    site_to_scrape_names_from = "https://suredbits.com/api/nfl/team/"
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = Request(site_to_scrape_names_from, headers=hdr)


    with urllib.request.urlopen(req) as url:
        r = url.read()

    soup = BeautifulSoup(r, 'html.parser')
    teams = soup.findAll("td", {"align": ["center", "left"]})
    for team in teams:
        if team['align']=='center':
            dict_one_team = {}
            dict_one_team['abbr']=team.string
        elif team['align']=='left':
            dict_one_team['name']=team.string
            dict_all_teams_abbr[dict_one_team['name']] = dict_one_team


    """
    We scrape the second site:
    Once we have the name of the team, we can scrape another site to get the the url of each team 
    (Each url is provided in the site in the next format):
    <a href="http://www.espn.com/nfl/team/_/name/ari/arizona-cardinals" class="bi">Arizona</a>               
    """
    site_to_scrape_ulrs = "http://www.espn.com/nfl/teams"
    req = Request(site_to_scrape_ulrs, headers=hdr)

    with urllib.request.urlopen(req) as url:
        r = url.read()

    dict_final = {}
    soup = BeautifulSoup(r, 'html.parser')
    links_url = soup.findAll("a", {"class": "bi"})
    for link in links_url:
        if link.string in dict_all_teams_abbr:
            dict_final[dict_all_teams_abbr[link.string]["abbr"]] =  link['href']
    return dict_final


"""
Sets the url field in the "node" variable if existing in the variable "url_of_all_teams" 
"""
def set_url_of_a_team(node,url_of_all_teams ):
    if node["id"] in url_of_all_teams:
        node["url"]=url_of_all_teams[node["id"]]


"""
Returns the number of players provided by each college
"""
def count_players_provided_by_each_college(results):
    college_and_players_provided = {}
    colleges = list(chain.from_iterable(results))
    # we groupe by college
    colleges_hash = toolz.groupby('college', colleges)
    for key, college in colleges_hash.items():
        college_name = key

        # we count the number of players provided by each college
        college_and_players_provided[college_name]=len(college)

    return college_and_players_provided


"""
Creates a json file with all the necessary information to be rendered in our html file 
"""
def create_final_json( occurrences, betweenness, closeness,  graph_info, json_all_info, count_players_each_college):
    nodes_with_info = []

    # we get the information of the url of all the teams
    url_of_all_teams = get_all_url_of_all_teams()

    # we create a dictionary as a referential variable to store all nodes and their indices
    dict_of_nodes_with_positions = {}

    # list to store he edges with their directions
    links_with_directions = []

    # we get the weight of each edge
    number_of_links_btw_nodes = count_weight(graph_info)

    existing_edges = set()

    for link in graph_info:
        dict_origin_target = {}

        key_weight = link[1] + link[0]

        if key_weight not in existing_edges:
            new_edge = True
            existing_edges.add(key_weight)
        else:
            new_edge = False

        # the information of the edge was provided in the info json as "target - source"
        if link[1] not in dict_of_nodes_with_positions:
            dict_of_nodes_with_positions[link[1]] = len(dict_of_nodes_with_positions)
            nodes_with_info.append(create_node_with_info(link[1], occurrences, betweenness,
                        closeness, url_of_all_teams,count_players_each_college))
        dict_origin_target["source"] = dict_of_nodes_with_positions[link[1]]

        if link[0] not in dict_of_nodes_with_positions:
            dict_of_nodes_with_positions[link[0]] = len(dict_of_nodes_with_positions)
            nodes_with_info.append(create_node_with_info(link[0], occurrences, betweenness,
                                            closeness, url_of_all_teams, count_players_each_college))

        dict_origin_target["target"] = dict_of_nodes_with_positions[link[0]]
        dict_origin_target["weight"] = number_of_links_btw_nodes[key_weight]
        if new_edge :
            links_with_directions.append(dict_origin_target)

    final_dict = {}
    final_dict["directed"] =False
    final_dict["graph"] = {}
    final_dict["nodes"] = nodes_with_info
    final_dict["links"] = links_with_directions
    final_dict["multigraph"] = False
    create_output_file(json_all_info, final_dict)


"""
Returns the number of connections between a team and college 
(this function is necessary so that we can add weights to the edges)
"""
def count_weight(edges):
    list_of_occurrences  = []
    for edge in edges:
        list_of_occurrences.append(edge[1]+edge[0])
    return collections.Counter(list_of_occurrences)


"""
Creates centrality information (betweenness, closeness...), outputs it to a json file with all the necessary 
information to be rendered in our html file
"""
def create_centrality_info(json_input_path,  json_all_info ):
    # we load the data taken from the API
    with open(json_input_path,'r', errors='ignore') as nfl:
        results = json.load(nfl)
    # we initialize a dict so as to store the occurrences of each node
    occurrences = {}

    # we create a variable to store the tuples corresponding to each of the edges - source, target -
    graph_info = create_graph_connections(results,  occurrences)

    # with the help of networkx, we create a graph to do all the calculations related with the closeness measures
    NFLGraph = create_graph(graph_info)
    closeness = nx.degree_centrality(G=NFLGraph)
    betweenness = nx.betweenness_centrality(G=NFLGraph)

    # this information will be usefull to be displayed as a tooltip of each college to show the
    #  sum of players provided by each college
    count_players_each_college = count_players_provided_by_each_college(results)
    create_final_json(occurrences, betweenness, closeness,  graph_info, json_all_info, count_players_each_college)



if __name__ == "__main__":
    json_input_path = "nflresults.json"
    json_all_info = "data/allInfo.json"
    start_time = time.time()
    create_centrality_info(json_input_path,  json_all_info )
    print("The execution took: {0:0.2f} seconds".format(time.time() - start_time))