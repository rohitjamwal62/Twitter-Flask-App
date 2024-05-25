import requests,json,os,configparser
from typing import List, Dict, Any
import time
data_list = list()
config_file = os.path.abspath('./dev_mode.ini' if os.path.exists('./dev_mode.ini') else './config.ini')
config = configparser.ConfigParser()
config.read(config_file)
BEARER_TOKEN = config.get('Twitter', 'bearer_token', raw=True)
REQUEST_LIMIT = 75
REQUEST_WINDOW = 15 * 60  # 15 minutes in seconds

def countdown(seconds):
    while seconds:
        mins, secs = divmod(seconds, 60)
        timeformat = f'{mins:02d}:{secs:02d}'
        print(f'Time left: {timeformat}', end='\r')
        time.sleep(1)
        seconds -= 1
    print('Resuming requests...\n')

def handle_rate_limit(response):
    if response.status_code == 429:
        print(f"Rate limit exceeded. Pausing for {countdown(REQUEST_WINDOW)}")
        return True  # Indicate rate limit hit
    return False  # Rate limit not hit

def Get_Likes(tweet_id):
    store_list = list()
    headers = {'Authorization': f'Bearer {BEARER_TOKEN}', 'Content-Type': 'application/json'}
    response = requests.get(f'https://api.twitter.com/2/tweets/{tweet_id}/liking_users', headers=headers)
    if handle_rate_limit(response):
        # Retry request after rate limit pause
        response = requests.get(f'https://api.twitter.com/2/tweets/{tweet_id}/liking_users', headers=headers)
    if response.status_code == 200:
        data = response.json().get('data', [])
        if not data:
            store_list.append({"Likedby_id": '', "Likedby_name": '', "Likedby_username": ''})
        else:
            for count, like in enumerate(data, start=1):
                context = {"Likedby_id": like.get('id'), "Likedby_name": like.get('name'), "Likedby_username": like.get('username')}
                store_list.append(context)
                print(count,": Likes. Tweet Id : ", tweet_id)
                if count >= 10:
                    print("Likes Break")
                    break
    else:
        print("Error Likes:", response.status_code)
        context = {"Likedby_id": '', "Likedby_name": '', "Likedby_username": ''}
        store_list.append(context)
    return store_list

def Get_Retweet(tweet_id):
    store_list = list()
    headers = {'Authorization': f'Bearer {BEARER_TOKEN}', 'Content-Type': 'application/json'}
    response = requests.get(f'https://api.twitter.com/2/tweets/{tweet_id}/retweeted_by', headers=headers)
    if handle_rate_limit(response):
        # Retry request after rate limit pause
        response = requests.get(f'https://api.twitter.com/2/tweets/{tweet_id}/retweeted_by', headers=headers)
    if response.status_code == 200:
        data = response.json().get('data', [])
        if not data:
            store_list.append({"retweetedby_id": '', "retweetedby_name": '', "retweetedby_username": ''})
        else:
            for count, tweet in enumerate(data, start=1):
                context = {"retweetedby_id": tweet.get('id'), "retweetedby_name": tweet.get('name'), "retweetedby_username": tweet.get('username')}
                store_list.append(context)
                print(count,": Retweets. Tweet Id : ", tweet_id)
                if count >= 10:
                    print("Retweet Break")
                    break
    else:
        print("Error Retweet:", response.status_code)
        context = {"retweetedby_id": '', "retweetedby_name": '', "retweetedby_username": ''}
        store_list.append(context)
    return store_list

def read_output_file(space_id: str, data_list: List[Dict[str, Any]]) -> None:
    file_path = os.path.join('output', space_id, 'user_topic_descriptions.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            read_json = file.read()
            json_records = json.loads(read_json)
            for key, value in json_records.items():
                for count,tweet_data in enumerate(value,start=1):
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
                    if count > 150:
                        print(f"Break Tweet Loop at {count}")
                        break
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except IOError as e:
        print(f"An error occurred while reading the file: {e}")