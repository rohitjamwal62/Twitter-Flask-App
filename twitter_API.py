import requests,json,os,configparser

config_file = os.path.abspath('./dev_mode.ini' if os.path.exists('./dev_mode.ini') else './config.ini')
config = configparser.ConfigParser()
config.read(config_file)
BEARER_TOKEN = config.get('Twitter', 'bearer_token', raw=True)


def Get_Likes(tweet_id):
    store_list = list()
    headers = {'Authorization': f'Bearer {BEARER_TOKEN}','Content-Type': 'application/json'}
    liking_users_response = requests.get(f'https://api.twitter.com/2/tweets/{tweet_id}/liking_users', headers=headers)
    if liking_users_response.status_code == 200:
        response = liking_users_response.json().get('data', [])
        if liking_users_response.json().get('meta'):
            Like_data = liking_users_response.json().get('meta').get('result_count')
            if Like_data == 0:
                context = {"Likedby_id" : '',"Likedby_name" : '',"Likedby_username" : ''}
                store_list.append(context)
        for Like in response:
            context = {"Likedby_id" : Like.get('id'),"Likedby_name" : Like.get('name'),"Likedby_username" : Like.get('username')}
            store_list.append(context)
    else:
        print("Error Likes:", liking_users_response.status_code)
        context = {"Likedby_id" : '',"Likedby_name" : '',"Likedby_username" : ''}
        store_list.append(context)
    return store_list 
        
        
def Get_Retweet(tweet_id):
    store_list = list()
    headers = {'Authorization': f'Bearer {BEARER_TOKEN}','Content-Type': 'application/json'}
    liking_users_response = requests.get(f'https://api.twitter.com/2/tweets/{tweet_id}/retweeted_by', headers=headers)
    if liking_users_response.status_code == 200:
        response = liking_users_response.json().get('data', [])
        if liking_users_response.json().get('meta'):
            tweet_data = liking_users_response.json().get('meta').get('result_count')
            if tweet_data == 0:
                context = {"tweetedby_id" : '',"tweetedby_name" : '',"tweetedby_username" : ''}
                store_list.append(context)
        for tweet in response:
            context = {"tweetedby_id" : tweet.get('id'),"tweetedby_name" : tweet.get('name'),"tweetedby_username" : tweet.get('username')}
            store_list.append(context)
    else:
        print("Error Retweet:", liking_users_response.status_code)
        context = {"tweetedby_id" : '',"tweetedby_name" : '',"tweetedby_username" : ''}
        store_list.append(context)
    return store_list
