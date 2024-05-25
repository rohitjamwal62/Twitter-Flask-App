import requests,json,os,configparser
from typing import List, Dict, Any
data_list = list()

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
        for count,Like in enumerate(response,start=1):
            context = {"Likedby_id" : Like.get('id'),"Likedby_name" : Like.get('name'),"Likedby_username" : Like.get('username')}
            store_list.append(context)
            if count >=10:
                print(count,'break ho gya like')
                break
    else:
        print(" Likes API Limit Exceeded")
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
                context = {"retweetedby_id" : '',"retweetedby_name" : '',"retweetedby_username" : ''}
                store_list.append(context)
        for count,tweet in enumerate(response,start=1):
            context = {"retweetedby_id" : tweet.get('id'),"retweetedby_name" : tweet.get('name'),"retweetedby_username" : tweet.get('username')}
            store_list.append(context)
            if count >=10:
                print(count,'break ho gya retweet')
                break
    else:
        print(" Retweet API Limit Exceeded")
        context = {"retweetedby_id" : '',"retweetedby_name" : '',"retweetedby_username" : ''}
        store_list.append(context)
    return store_list


def read_output_file(space_id: str, data_list: List[Dict[str, Any]]) -> None:
    file_path = os.path.join('output', space_id, 'user_topic_descriptions.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            read_json = file.read()
            json_records = json.loads(read_json)
            for key, value in json_records.items():
                for tweet_data in value:
                    user_id = tweet_data.get('user_id')
                    tweet_id = tweet_data.get('tweet_id')
                    tweet_text = tweet_data.get('tweet_text')
                    date = tweet_data.get('date')
                    time = tweet_data.get('time')
                    # Append the relevant data to the list
                    data_list.append({
                        'user_id': user_id,
                        'tweet_id': tweet_id,
                        'tweet_text': tweet_text,
                        'date': date,
                        'time': time
                    })
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except IOError as e:
        print(f"An error occurred while reading the file: {e}")