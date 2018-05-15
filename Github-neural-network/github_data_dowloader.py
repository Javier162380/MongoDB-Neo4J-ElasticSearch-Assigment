import os
from time import sleep
from multiprocessing import Pool
from github import Github, GithubException
import json
from boto3 import client

def coalesce(username,userlogin):
    if username is None:
        return userlogin
    else:
        return username

def forker_name(name):
    if '/' in name:
        return name.split('/')[0]
    else:
        return None

def store_data(path,json_file, results):
    with open('{0}{1}.json'.format(path,json_file), 'w') as file:
        for registers in results:
            for result in registers:
                json.dump(result, file)
                file.write('\n')

def upload_s3_file(s3handler, file, s3file_name,bucket):
    file_object = open(file,'r').read()
    s3handler.put_object(Body=file_object, Bucket=bucket,Key=s3file_name)

def get_contributors_or_watchers(iterator):
    org_members = iterator[0]
    repository = iterator[1]
    repository_relation = iterator[2]
    repository_iterator = {
        'contributors': repository.get_contributors,
        'watchers': repository.get_watchers,
        'stargazers': repository.get_stargazers
    }[repository_relation]()

    github_results = []
    for user in repository_iterator:
        try:
            results = {'user': coalesce(user.login, user.name), 'user_type': 'member', 'repository': repository.name,
                       'repository_language': repository.language, 'repository_relation': repository_relation,
                       'repository_forks': repository.forks_count, 'repository_watchs': repository.watchers_count,
                       'repository_suscribers': repository.subscribers_count,
                       'repository_stars': repository.stargazers_count}
            results['user_type'] = 'member' if user.login in org_members else 'not_member'
            github_results.append(results)
        except GithubException.RateLimitExceededException:
            sleep(600)

    return github_results

def get_forkers(iterator):
    org_members = iterator[0]
    repository = iterator[1]
    forkers = []
    for user in repository.get_forks():
        try:
            forker = forker_name(user.full_name)
            results = {'user':forker , 'user_type': 'member', 'repository': repository.name,
                       'repository_language': repository.language, 'repository_relation': 'forkers',
                       'repository_forks': repository.forks_count, 'repository_watchs': repository.watchers_count,
                       'repository_suscribers': repository.subscribers_count,
                       'repository_stars': repository.stargazers_count}
            results['user_type'] = 'member' if forker in org_members else 'not_member'
            forkers.append(results)
        except GithubException.RateLimitExceededException:
            sleep(600)
    return forkers

def main():
    #assign credentials
    GithubUser = os.getenv('git_user')
    GithubPassword = os.getenv('git_password')
    aws_access_key_id = os.getenv('aws_public_key')
    aws_access_key_secret = os.getenv('aws_secret_key')
    #create a client object.
    github_client = Github(GithubUser, GithubPassword)
    #create a s3 client.
    s3_client = client('s3', aws_access_key_id=aws_access_key_id,
                       aws_secret_access_key=aws_access_key_secret)
    #get the organization members and repositories.
    org=github_client.get_organization(login = 'Python')
    org_members = [member.login for member in org.get_members()]
    org_repositories = [repository for repository in org.get_repos()]
    #we create an iterator to get the information we want
    contributors_repositories = ([org_members, repository,'contributors'] for repository in org_repositories)
    forkers_repositories = ([org_members, repository] for repository in org_repositories)
    watchers_repositories = ([org_members, repository, 'watchers'] for repository in org_repositories)
    stargazers_repositories = ([org_members, repository, 'stargazers'] for repository in org_repositories)

    executor = Pool(processes=3)
    #we create a pool of process
    contributors_results = executor.map_async(get_contributors_or_watchers,contributors_repositories)
    forkers_results = executor.map_async(get_forkers,forkers_repositories)
    watchers_results = executor.map_async(get_contributors_or_watchers,watchers_repositories)
    stargazers_results = executor.map_async(get_contributors_or_watchers, stargazers_repositories)
    executor.join()

    ##we store the results in our local machine just in case something goes wrong when we upload to s3.
    abs_path = os.path.dirname(os.path.realpath(__file__))+'/data/'
    store_data(abs_path,'contributors',[results for results in contributors_results])
    store_data(abs_path,'forkers',[results for results in forkers_results])
    store_data(abs_path,'watchers', [results for results in watchers_results])
    store_data(abs_path,'stargazers', [results for results in stargazers_results])
#
    ##we uplaod files to s3.
    for file in os.listdir(abs_path):
        print(file)
        if file.endswith(".json"):
            upload_s3_file(s3_client,file,s3file_name=file,bucket='github-tfm')

if __name__ == '__main__':
    main()
