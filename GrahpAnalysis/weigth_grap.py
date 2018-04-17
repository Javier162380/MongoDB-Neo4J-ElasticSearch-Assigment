# edges preparation
grahp_results = []
for team in teams_results:
    number_of_players = len(team)
    res = toolz.groupby('college', team)
    for key, value in res.items():
        weight_node = len(value) / number_of_players
        college_name = key
        team_name = team[0]['team']
        node_results = tuple([team_name, college_name, weight_node])
        grahp_results.append(node_results)
