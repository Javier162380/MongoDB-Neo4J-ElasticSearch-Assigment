import asyncio
import aiohttp
import json

async def download_nfl_player_data(team):
    async with aiohttp.ClientSession() as client:
        response = await client.request('GET','http://api.suredbits.com/nfl/v0/team/{0}/roster'.format(team))
        print(response)
        json_value_return = await response.json()
        return json_value_return

if __name__ == '__main__':

    teams=['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND',
           'JAC', 'KC','LA','MIA','MIN','NE','NO','NYG','NYJ','OAK','PHI','PIT','SD','SEA','SF','TB','WAS']

    #async donwload data.
    task = [asyncio.Task(download_nfl_player_data(team)) for team in teams]
    all_task = asyncio.gather(*task, return_exceptions=True)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(all_task)
    teams_results = [i.result() for i in task if i.exception() is None]

    #store data.
    with open('nflresults.json', 'w') as nfl:
        #for team in teams_results:
        json.dump(teams_results,nfl)
        nfl.write('\n')