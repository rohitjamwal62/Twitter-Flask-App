import pandas as pd
import json, requests, csv
import socket
from dependencies.sprint import *
import datetime
from time import sleep
TIME_TO_SLEEP_ON_FAILURE = 0  # in seconds
def extract_space_data_to_csv(space_data, destination_csv, array_to_text = True):
    """
    This function extracts user data from space_data, a JSON format data, and writes it into a CSV file.
    It first normalizes the JSON data into a pandas dataframe.
    Then, it reorders and renames the columns based on the definitions in user_data_columns_defs.
    Finally, it saves the dataframe into a CSV file located at destination_csv.

    Parameters:
    space_data (dict): A dictionary containing user data in JSON format
    destination_csv (str): The path of the output CSV file

    Returns:
    None
    """

    #* Column definitions for Space Data
    space_data_columns_defs = {
        "columns": [
                    "id",
                    "title",
                    "created_at",
                    "lang",
                    "creator_id",
                    "host_ids",
                    "invited_user_ids",
                    "participant_count",
                    "speaker_ids",
                    "start_date",
                    "start_time",
                    "state",
                    "updated_at",
                    "scheduled_start",
                    "is_ticketed",
                    "end_date",
                    "end_time",
                    "duration",
                    "topic_ids",
                    "topic_names",
                    "topic_desc",
                    "total_speakers",
                    "total_moderators",
                ],
        "rename_map" : {
            "host_ids": "Host Ids",
            "created_at": "Created At",
            "creator_id": "Creator Id",
            "id": "Space Id",
            "lang": "Language",
            "invited_user_ids": "Invited User Ids",
            "participant_count": "Participant Count",
            "speaker_ids": "Speaker Ids",
            "start_date": "Start Date",
            "start_time": "Start Time",
            "state": "State",
            "title": "Title",
            "updated_at": "Updated",
            "scheduled_start": "Scheduled Start",
            "is_ticketed": "Is Ticketed",
            "end_date": "End Date",
            "end_time": "End Time",
            "duration": "Duration",
            "topic_ids": "Topic Ids",
            "topic_names": "Topic Names",
            "topic_desc": "Topic Descriptions",
            "total_speakers": "Total Speakers",
            "total_moderators": "Total Moderators",
        },
        "expand": ['topic_ids', 'topic_names', 'topic_desc']
    }

    space_data_df = pd.json_normalize(space_data)
    space_data_columns_defs["columns"] = [col for col in space_data_columns_defs["columns"] if col in space_data_df]
    # sprint_vars(space_data_columns_defs)
    #step Reorder and remove columns
    if "columns" in space_data_columns_defs:
        space_data_df = space_data_df[space_data_columns_defs["columns"]]


    #step Expand fields into columns
    if "expand" in space_data_columns_defs:
        for key in space_data_columns_defs["expand"]:
            if key in space_data_df and not space_data_df[key].empty and all(isinstance(item, list) and item for item in space_data_df[key]):
                new_columns = [f"{key}_{i + 1}" for i in range(len(space_data_df[key].iloc[0]))]
                space_data_df[new_columns] = space_data_df[key].apply(lambda x: pd.Series(x) if x else pd.Series([None] * len(new_columns)))

                space_data_df = space_data_df.drop([key], axis=1, errors='ignore')

    #step Convert arrays to text
    if array_to_text:
        for col in space_data_df.columns:
                space_data_df[col] = space_data_df[col].apply(lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x)

    #step Rename columns
    if "rename_map" in space_data_columns_defs:
        space_data_df.rename(columns=space_data_columns_defs["rename_map"], inplace=True)

    #step Remove empty columns
    space_data_df = space_data_df.dropna(axis=1, how='all')

    #step Save data to CSV file in relative output dir
    sprintSaveCSV(space_data_df, destination_csv, quoting=csv.QUOTE_NONNUMERIC)



def extract_space_user_data_to_csv(space_users_data, destination_csv, array_to_text=True):
    """
    This function extracts user data from space_users_data, a JSON format data, and writes it into a CSV file.
    It first normalizes the JSON data into a pandas dataframe.
    Then, it reorders and renames the columns based on the definitions in user_data_columns_defs.
    Finally, it saves the dataframe into a CSV file located at destination_csv.

    Parameters:
    space_users_data (dict): A dictionary containing user data in JSON format
    destination_csv (str): The path of the output CSV file

    Returns:
    None
    """
    #* Column definitions for Space Users Data
    user_data_columns_defs = {
        "columns": [
                'space_id',
                'user_id', 'name', 'username', 'created_at_date',
                'created_at_time', 'location', 'protected',
                'description', 'pinned_tweet_id',
                'public_metrics.followers_count',
                'public_metrics.following_count',
                'public_metrics.tweet_count',
                'public_metrics.listed_count',
                'public_metrics.like_count',
                'followers_from_current_space',
                'following_from_current_space',
                'followers',
                'followings',
                ],
        "rename_map" : {
                'space_id':"Space Id",
                'user_id':"User ID",
                'followers_from_current_space':'Followers From Current Space',
                'following_from_current_space':'Following From Current Space',
                'followers':'Followers',
                'followings':'Followings',
                'public_metrics.followers_count': 'Followers Count',
                'public_metrics.following_count': 'Following Count',
                'public_metrics.tweet_count': 'Tweet',
                'public_metrics.listed_count': 'Listed',
                'public_metrics.like_count': 'Likes',
                'pinned_tweet_id': 'Pinned Tweet Id'
        }
    }
    space_users_data_df = pd.json_normalize(space_users_data)
    user_data_columns_defs["columns"] = [col for col in user_data_columns_defs["columns"] if col in space_users_data_df]
    #step Reorder and remove columns
    if "columns" in user_data_columns_defs:
        space_users_data_df = space_users_data_df[user_data_columns_defs["columns"]]
    #step Rename columns
    if "rename_map" in user_data_columns_defs:
        space_users_data_df.rename(columns=user_data_columns_defs["rename_map"], inplace=True)
    #step Convert arrays to text
    if array_to_text:
        for col in space_users_data_df.columns:
                space_users_data_df[col] = space_users_data_df[col].apply(lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x)

    #step Remove empty columns
    space_users_data_df = space_users_data_df.dropna(axis=1, how='all')
    #step Save data to CSV file in relative output dir
    sprintSaveCSV(space_users_data_df,destination_csv, quoting=csv.QUOTE_NONNUMERIC)


def extract_ids_from_json(json_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            user_ids = [item['user_id'] for item in data]
            return user_ids
    except Exception as e:
        sprint(f"Error: {e}",Type="error")
        error_info = traceback.format_exc()
        sprint(error_info)
        return []

def extract_all_annotations(user_tweets):
    # function to pick just one topic and description from the annotation

    data = {
        "domain_id": [],
        "domain_name": [],
        "domain_description": [],
        "entity_id": [],
        "entity_name": [],
        "entity_description": []
    }

    for tweet in user_tweets:
        context_annotations = tweet.get('context_annotations', [])
        for ctx in context_annotations:
            domain = ctx.get('domain', {})
            entities = ctx.get('entity', {})
            if 'id' in domain:
                data['domain_name'].append(domain.get('name', ''))
                data['domain_id'].append(domain.get('id', ''))
                data['domain_description'].append(domain.get('description', ''))
            if 'id' in entities:
                data['entity_name'].append(entities.get('name', ''))
                data['entity_id'].append(entities.get('id', ''))
                data['entity_description'].append(entities.get('description', 'N/A'))
    return data

def get_topic_details_by_ids(topic_ids_str, json_data):
    topic_ids = [topic_id.strip() for topic_id in topic_ids_str.split(',')]
    results = []
    for topic_id in topic_ids:
        found_topic = next(
            (topic for topic in json_data.get('includes', {}).get('topics', []) if topic['id'] == topic_id),
            None)
        if found_topic:
            results.append(
                {'id': topic_id, 'name': found_topic['name'], 'description': found_topic['description']})
        else:
            results.append({'id': topic_id, 'error': 'Topic not found'})
    return results

def fetch_tweets_and_annotations(user_ids, max_results, BEARER_TOKEN, output_json_file):

    def _get_tweets(user_id):

        headers = {
            'Authorization': f'Bearer {BEARER_TOKEN}'
        }
        url = f'https://api.twitter.com/2/users/{user_id}/tweets?tweet.fields=context_annotations,created_at&max_results={max_results}'

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        elif response.status_code == 429:
            reset_time = int(response.headers.get('x-rate-limit-reset'))
            reset_time_readable = datetime.datetime.fromtimestamp(reset_time)
            sprint(f"Rate limit will reset at: {reset_time_readable}", Type="alert")

            current_time = datetime.datetime.now()
            sleep_time = (reset_time_readable - current_time).total_seconds()

            # Sleep until the rate limit resets
            if sleep_time > 0:
                for x in range(int(sleep_time), 0, -1):
                    minutes, seconds = divmod(x, 60)
                    if minutes > 0:
                        sprint(f"Therefore, sleeping for {minutes} minutes, {seconds} seconds...", end="\r")
                    else:
                        sprint(f"Therefore, sleeping for {seconds} seconds...", end="\r")
                    sleep(1)
            return _get_tweets(user_id)
        else:
            sprint(f"Error {response.status_code} for user {user_id}: {response.text}",Type="alert")

    user_tweets = {}

    for user_id in user_ids:
        user_tweets[user_id] = _get_tweets(user_id)
    # Process user_tweets to extract a single topic and description for each user
    user_topic_descriptions = {}
    for user_id, tweets in user_tweets.items():
        user_topic_descriptions[user_id] = []

        for tweet in tweets:
            context_annotations = tweet.get('context_annotations', [{}])
            for ctx in context_annotations:
                domain = ctx.get('domain', {})
                entities = ctx.get('entity', {})
                user_topic_descriptions[user_id].append({
                    'user_id': user_id,
                    'tweet_id': str(tweet['id']),
                    'tweet_text': tweet['text'],
                    'date': tweet['created_at'].split('T')[0],
                    'time': tweet['created_at'].split('T')[1].split(".")[0],
                    'domain_id':domain.get('id', ''),
                    'domain_name':domain.get('name', ''),
                    'domain_description':domain.get('description', ''),
                    'entity_id':entities.get('id', ''),
                    'entity_name':entities.get('name', ''),
                    'entity_description':entities.get('description', ''),
                })

    # Write the result to the output JSON file
    with open(output_json_file, 'w', encoding='utf-8') as json_file:
        json.dump(user_topic_descriptions, json_file, ensure_ascii=False, indent=4)

    # iterate through dict user_topic_descriptions
    csv_data = []
    for user_id, data in user_topic_descriptions.items():
        # add data list to csv_data
        csv_data.extend(data)

    #create dataframe and save as csv
    df = pd.DataFrame(csv_data)
    sprintSaveCSV(df, output_json_file.replace(".json", ".csv"))


def check_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(starting_port=5000):
    port = starting_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:  # Port is available
                return port
            port += 1  # Try the next port