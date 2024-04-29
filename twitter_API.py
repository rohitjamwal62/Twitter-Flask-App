import requests,json,os,configparser

config_file = os.path.abspath('./dev_mode.ini' if os.path.exists('./dev_mode.ini') else './config.ini')
config = configparser.ConfigParser()
config.read(config_file)
BEARER_TOKEN = config.get('Twitter', 'bearer_token', raw=True)

def get_tweet_interaction_users(tweet_id):
    headers = {'Authorization': f'Bearer {BEARER_TOKEN}','Content-Type': 'application/json'}
    # Get liking users
    liking_users_response = requests.get(f'https://api.twitter.com/2/tweets/{tweet_id}/liking_users', headers=headers)
    liking_users_data = liking_users_response.json()
    # Get retweeted by users
    retweeted_by_response = requests.get(f'https://api.twitter.com/2/tweets/{tweet_id}/retweeted_by', headers=headers)
    retweeted_by_data = retweeted_by_response.json()
    return liking_users_data, retweeted_by_data

