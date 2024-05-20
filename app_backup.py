# Standard Library Imports
import csv
import json
from io import StringIO
import zipfile
import secrets
import tempfile
import webbrowser
from datetime import timedelta
# Third-party Library Imports
from flask import Flask, render_template, request, jsonify, send_file
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler
# Local Imports
from dependencies.sprint import *
from definitions.functions import *
from definitions.scraper import *
from twitter_API import Get_Likes,Get_Retweet,read_output_file,data_list
#! INTERNAL STUFF BELOW DO NOT MODIFY
from itertools import zip_longest

#region Setup Variables and constants
global search_term, spacedata_json_file, user_topic_descriptions_json_file
REV_NUM = '25/2/24/1'


config_file = os.path.abspath('./dev_mode.ini' if os.path.exists('./dev_mode.ini') else './config.ini')
config = ConfigParser()
config.read(config_file)

max_results = int(config.get('Twitter', 'tweets_max_results', fallback='50'))
HOSTNAME = config.get('Setup', 'hostname', fallback='localhost')
PORT = int(config.get('Setup', 'port', fallback='8000'))
BEARER_TOKEN = config.get('Twitter', 'bearer_token', raw=True)
SCRAPE_USER_DATA = True if config.get('Twitter', 'get_users_following_data', fallback='true').lower() == 'true' else False
GET_TWEETS_DATA = True if config.get('Twitter', 'get_tweets_data', fallback='true').lower() == 'true' else False


OUTPUT_DIR = config.get('Setup', 'output_files_dir', fallback='output')
#! Creating Output Directory
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

json_file_path = os.path.join(OUTPUT_DIR, config.get('Setup', 'space_id_json'))

#endregion


#! Flask app setup below

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)

scheduler = BackgroundScheduler()
scheduler.start()

Main_Records = list()
@app.route('/',)
def homes():
    """
    Defines a route for the root URL ("/") of the application.

    Returns:
        The rendered template for the "index.html" page.
    """
    return render_template('index.html')


@app.route('/download_csv')
def download_csv():
    global Main_Records
    print(Main_Records,"+++++++++++++++")
    csv_header = ['tweet_id', 'tweet_text', 'date', 'time', 'Likedby_id', 'Likedby_username', 'Likedby_name', 'retweetedby_name', 'retweetedby_id', 'retweetedby_username']
    with open('user_likes_retweets.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_header)
        writer.writeheader()
        for tweet_csv in Main_Records:
            for user_id, tweets in tweet_csv.items():
                for tweet_data in tweets:
                    writer.writerow({
                        'tweet_id': tweet_data['tweet_id'],
                        'tweet_text': tweet_data['tweet_text'],
                        'date': tweet_data['date'],
                        'time': tweet_data['time'],
                        'Likedby_id': ','.join(tweet_data['Likedby_id']),
                        'Likedby_username': ','.join(tweet_data['Likedby_username']),
                        'Likedby_name': ','.join(tweet_data['Likedby_name']),
                        'retweetedby_name': ','.join(tweet_data['retweetedby_name']),
                        'retweetedby_id': ','.join(tweet_data['retweetedby_id']),
                        'retweetedby_username': ','.join(tweet_data['retweetedby_username'])
                    })
                    
    return send_file('user_likes_retweets.csv', as_attachment=True)


@app.route('/download_json')
def download_json():
    global Main_Records
    with open('user_likes_retweets.json', 'w') as jsonfile:
        json.dump(Main_Records, jsonfile, indent=4)
    return send_file('user_likes_retweets.json', as_attachment=True)

@app.route('/searchSpaces', methods=['GET', 'POST'])
def search_spaces():
    data_list = list()
    global search_term, spacedata_json_file, user_topic_descriptions_json_file,Main_Records
    #* Getting Params
    quick_mode = request.args.get('quick_mode')
    search_by = request.args.get('by')
    search_term = request.form["search_term"]
    spacedata_json_file = os.path.join(OUTPUT_DIR, search_term, 'space_user_data.json')
    user_topic_descriptions_json_file = os.path.join(OUTPUT_DIR, search_term, 'user_topic_descriptions.json')


    try:
        if request.method == 'POST':
            params = {
                        "expansions": "host_ids,topic_ids,invited_user_ids,creator_id,speaker_ids",
                        "space.fields": "created_at,lang,invited_user_ids,participant_count,scheduled_start,started_at,title,topic_ids,updated_at,speaker_ids,ended_at",
                        "user.fields": "created_at,description,entities,id,location,name,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,verified_type,withheld",
            }
            if search_by == "space_title":
                params["query"] = search_term
            elif search_by == "creator_id":
            
                params["user_ids"] = search_term

            headers = {
                "Authorization": f"Bearer {BEARER_TOKEN}",
                "Content-Type": "application/json",
            }
            api_url = "https://api.twitter.com/2/spaces/"

            if search_by == "space_id":
                api_url = api_url +  search_term
            elif search_by == "space_title":
                api_url = api_url + "search"
            elif search_by == "creator_id":
                api_url = api_url + "by/creator_ids"

            # sprint_vars(api_url, params, headers, search_by)
            response = requests.get(api_url, headers=headers, params=params)

            if response.status_code == 200:
                #create search_term directory inside OUTPUT_DIR
                if not os.path.exists(os.path.join(OUTPUT_DIR,search_term)):
                    os.mkdir(os.path.join(OUTPUT_DIR,search_term))
                data = response.json()
                
                print("#########################################################################")
                # *************************************  Rekha Code Start Here  ********************************************
                Space_Id_Store_Here = search_term
                print("Space Id : ",Space_Id_Store_Here)
                read_output_file(Space_Id_Store_Here, data_list)
                print("data_list hai bro ye.............",data_list)
                user_tweets = list()
                tweet_data_dict = dict()
                unique_tweet_ids = set()
                for tweet in data_list:
                    Tweet_Id = tweet.get('tweet_id')
                    if Tweet_Id in unique_tweet_ids:
                        continue  # Skip this tweet if it's a duplicate
                    unique_tweet_ids.add(Tweet_Id)

                    user_id =  tweet.get('user_id')
                    tweet_text = tweet.get('tweet_text')
                    date = tweet.get('date')
                    time = tweet.get('time')
                    Like_users = Get_Likes(Tweet_Id)
                    Retweet_users = Get_Retweet(Tweet_Id)
                    tweet_data = {
                        "tweet_id": Tweet_Id,
                        "tweet_text": tweet_text,
                        "date": date,
                        "time": time,
                        "Likedby_id": [],
                        "Likedby_username": [],
                        "Likedby_name": [],
                        "retweetedby_name": [],
                        "retweetedby_id": [],
                        "retweetedby_username": []
                    }
                    if Like_users is not None:
                        liked_by_ids = [like.get('Likedby_id', '') for like in Like_users]
                        liked_by_usernames = [like.get('Likedby_username', '') for like in Like_users]
                        liked_by_names = [like.get('Likedby_name', '') for like in Like_users]
                        tweet_data['Likedby_id'] = liked_by_ids
                        tweet_data['Likedby_username'] = liked_by_usernames
                        tweet_data['Likedby_name'] = liked_by_names
                    if Retweet_users is not None:
                        retweeted_by_ids = [retweet.get('retweetedby_id', '') for retweet in Retweet_users]
                        retweeted_by_usernames = [retweet.get('retweetedby_username', '') for retweet in Retweet_users]
                        retweeted_by_names = [retweet.get('retweetedby_name', '') for retweet in Retweet_users]
                        tweet_data['retweetedby_id'] = retweeted_by_ids
                        tweet_data['retweetedby_username'] = retweeted_by_usernames
                        tweet_data['retweetedby_name'] = retweeted_by_names
                    
                    else:
                        tweet_data['Likedby_id'] = []
                        tweet_data['Likedby_username'] = []
                        tweet_data['Likedby_name'] = []
                        tweet_data['retweetedby_id'] = []
                        tweet_data['retweetedby_username'] = []
                        tweet_data['retweetedby_name'] = []

    
                    if user_id not in tweet_data_dict:
                        tweet_data_dict[user_id] = []

                    tweet_data_dict[user_id].append(tweet_data)
                 
                Main_Records.append(tweet_data_dict)     
                print("\n")
                print("#########################################################################")
                # *************************************   Rekha Code End Here   ********************************************
                
                #* Detect errors 
                if "errors" in data:
                    return render_template('index.html', error_message=str(data["errors"][0]["detail"]), search_term=search_term)

                #* If search by space_title or creator_id
                results_count = data.get("meta", {}).get("result_count", None)
                if results_count == 0:
                    return render_template('index.html', error_message="No results found", search_term=search_term)

                #region Extracting Spaces Data
                space_all_details = data.get("data", {} if search_by=="space_id" else [])
                if type(space_all_details) != list:
                    space_all_details = [space_all_details]
                topics_all_details = data.get('includes', {}).get('topics', [])
                for space_data in space_all_details:
                    if "speaker_ids" in space_data:
                        space_data["total_speakers"] = len(space_data["speaker_ids"])
                    if "host_ids" in space_data:
                        space_data["total_moderators"] = len(space_data["host_ids"])
                    if "topic_ids" in space_data:
                        space_data["topic_names"] = [topic.get("name") for topic in topics_all_details if topic["id"] in space_data["topic_ids"] and "name" in topic]

                        space_data["topic_desc"] = [topic.get("description") for topic in topics_all_details if topic["id"] in space_data["topic_ids"] and "description" in topic]

                    if "started_at" in space_data and "ended_at" in space_data:
                        time_diff = (datetime.strptime(space_data["ended_at"], "%Y-%m-%dT%H:%M:%S.%fZ") - datetime.strptime(space_data["started_at"], "%Y-%m-%dT%H:%M:%S.%fZ")).total_seconds()
                        space_data["duration"] = str(timedelta(seconds=int(time_diff)))
                    if "started_at" in space_data:
                        space_data["start_date"] = space_data["started_at"].split("T")[0]
                        space_data["start_time"] = space_data["started_at"].split("T")[1].split(".")[0]
                        del space_data["started_at"]
                    if "ended_at" in space_data:
                        space_data["end_date"] = space_data["ended_at"].split("T")[0]
                        space_data["end_time"] = space_data["ended_at"].split("T")[1].split(".")[0]
                        del space_data["ended_at"]
                #* Save Space Data to JSON file
                with open(os.path.join(OUTPUT_DIR,search_term,"space_data.json"), "w") as file:
                    json.dump(space_all_details, file, indent=3)

                #* Save Space Data to CSV file
                extract_space_data_to_csv(space_all_details, os.path.join(OUTPUT_DIR,search_term,f"space_data.csv"))
                #endregion


                #! Scrape User Data and Annotations only if search_by is space_id
                if search_by == "space_id":
                    #region Extracting Spaces Users Data
                    space_users_data = data.get('includes', {}).get('users', [])
                    space_user_fields = {
                        'user_id': 'id',
                        'name': 'name',
                        'username': 'username',
                        'created_at': 'created_at',
                        'location': 'location',
                        'protected': 'protected',
                        'public_metrics': 'public_metrics',
                        'pinned_tweet_id':'pinned_tweet_id',
                        'description': 'description',
                        'url': 'url',
                    }

                    user_data = []
                    for user in space_users_data:

                        formatted_user = { 'space_id': search_term,  }
                        # rename user fields
                        for key, value in space_user_fields.items():
                            formatted_user[key] = user.get(value, '')

                        if "pinned_tweet_id" in formatted_user:
                            formatted_user['pinned_tweet_id'] = str(formatted_user['pinned_tweet_id'])
                        # convert user_id to string
                        if "user_id" in formatted_user:
                            formatted_user['user_id'] = str(formatted_user['user_id'])
                        # split created_at into date and time
                        if "created_at" in formatted_user:
                            formatted_user['created_at_date'] = formatted_user['created_at'].split("T")[0]
                            formatted_user['created_at_time'] = formatted_user['created_at'].split("T")[1].split(".")[0]
                            del formatted_user["created_at"]
                        user_data.append(formatted_user)
                    
                    #* Save User Data to JSON file
                    with open(os.path.join(OUTPUT_DIR,search_term,"space_user_data.json"), "w") as space_user_file:
                        json.dump(user_data, space_user_file, indent=3)
                    #region getting followers and following list
                    if not quick_mode and SCRAPE_USER_DATA:
                        all_usernames = [user['username'] for user in user_data]
                        user_follow_data, status = get_twitter_follows(all_usernames)
                        # * adding to user_data and then saving user data again
                        for user in user_data:
                            if user['username'] in user_follow_data:
                                user['followers'] = user_follow_data[user['username']]['followers']
                                user['following'] = user_follow_data[user['username']]['following']
                                #* adding followers_from_current_space, following_from_current_space columns
                                user['followers_from_current_space'] = [user_details for user_details in user['followers'] if user_details["username"] in all_usernames]
                                user['following_from_current_space'] = [user_details for user_details in user['following'] if user_details["username"] in all_usernames]

                        #* Save User Data to JSON file again
                        with open(os.path.join(OUTPUT_DIR,search_term,"space_user_data.json"), "w") as space_user_file:
                            json.dump(user_data, space_user_file, indent=3)
                    #endregion


                    #* Save User Data to CSV file
                    extract_space_user_data_to_csv(user_data, os.path.join(OUTPUT_DIR,search_term,f"space_user_data.csv"))
                    #endregion


                    #region getting tweets and annotations
                    if not quick_mode and GET_TWEETS_DATA:
                        sprint("Getting tweet data (This might take a while, if rate limited)")
                        user_ids = extract_ids_from_json(spacedata_json_file)
                        fetch_tweets_and_annotations(user_ids, max_results, BEARER_TOKEN, user_topic_descriptions_json_file)
                    #endregion

                return render_template('/results.html', search_by=search_by, search_term=search_term)

            else:
                print(f"Error: {response.status_code}, {response.text}")
                return render_template('index.html', error_message=f"Error {response.status_code}: {response.text}", search_term=search_term)
        else:
            return render_template('index.html')
    except Exception as e:
        sprint(f"Error: {e}",Type="error")
        error_info = traceback.format_exc()
        sprint(error_info)
        return render_template('index.html', error_message=str(e), search_term=search_term)



# #region Results routes
# @app.route('/results.html')
# def reports():
#     return render_template('results.html')

# #endregion

#region Getting extracted data for entered search_term in UI, this data has been already dumped as json
@app.route('/get_space_data')
def get_space_data():
    file = os.path.join(OUTPUT_DIR,search_term,"space_data.json")
    data = {}
    if os.path.exists(file):
        with open(file, 'r',encoding='utf-8') as f:
            data = json.load(f)
    return jsonify(data)

@app.route('/get_space_user_data')
def get_space_user_data():
    file = os.path.join(OUTPUT_DIR,search_term,"space_user_data.json")
    data = {}
    if os.path.exists(file):
        with open(file, 'r',encoding='utf-8') as f:
            data = json.load(f)
    return jsonify(data)

@app.route('/get_tweets')
def annotation():
    file = os.path.join(OUTPUT_DIR,search_term,"user_topic_descriptions.json")
    data = {}
    if os.path.exists(file):
        with open(file, 'r',encoding='utf-8') as f:
            data = json.load(f)
    return jsonify(data)

#endregion

#region Endpoints for downloading data files
@app.route('/download')
def download():

    data_type = request.args.get('type')

    if data_type is None:
        return "Invalid download type"

    if data_type == "all_data":
        files_to_download = ['space_data.json', 'space_data.csv', 'space_user_data.csv', 'space_user_data.json']

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file in files_to_download:
                    if os.path.exists(os.path.join(OUTPUT_DIR, search_term, file)):
                        zip_file.write(os.path.join(OUTPUT_DIR, search_term, file), arcname=file)
            return send_file(temp_zip.name, as_attachment=True, download_name=f'{search_term}_data.zip')

    num_dots = data_type.count('.')
    if num_dots > 1:
        return "Invalid download type"
    filename = data_type.split('.')[0]
    filetype = data_type.split('.')[1]
    if not filetype in ['json', 'csv']:
        return "Invalid download type"
    file = os.path.join(OUTPUT_DIR,search_term,filename+'.'+filetype)
    if os.path.exists(file):
        return send_file(file, as_attachment=True, download_name=f"{search_term}_{data_type}")
    else:
        return "File not found"


#endregion


def update_or_create_worksheet(spreadsheet, worksheet_name, csv_contents):
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(worksheet_name, rows=100, cols=22)

        worksheet.clear()


        # values = [csv.split('"') for csv in csv_contents.split('\n')]
        reader = csv.reader(StringIO(csv_contents))
        values = [row for row in reader]
        worksheet.update(values=values, range_name=None)


@app.route('/send_to_google_sheets')
def spreadsheets():
    scope = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    google_auth_file = os.path.join(config.get('Setup', 'temp_dir', fallback="temp"), "google.json")

    if not os.path.exists(google_auth_file):
        return jsonify({'message': 'Google Auth file not found', 'status': 'error'})
    creds = ServiceAccountCredentials.from_json_keyfile_name(google_auth_file, scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open("space user")

    files_to_upload = ['space_data.csv', 'space_user_data.csv']
    for file in files_to_upload:
        filepath = os.path.join(OUTPUT_DIR, search_term, file)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding="utf-8") as csv:
                data = csv.read()
                update_or_create_worksheet(spreadsheet, f"{search_term}_{file.replace('.csv', '')}", data)

    return jsonify({'message': 'Uploaded to Google Sheets', 'status': 'success'})

scheduler.add_job(spreadsheets, 'interval', hours=24)



if __name__ == "__main__":

    if check_port_in_use(PORT):
        print(f"Port {PORT} is already in use. Please ensure the port is available or specify a different port.")
        # You can choose to exit the script or use a different port
        exit(1)
    else:
        webbrowser.open_new(f'http://{HOSTNAME}:{PORT}/')
        app.run(host=HOSTNAME, port=PORT)