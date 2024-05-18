import os
import json
from typing import List, Dict, Any

def read_output_file(space_id: str, data_list: List[Dict[str, Any]]) -> None:
    if space_id == "1vOGwjWRnjbKB":
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

# Example usage
data_list = []
read_output_file("1vOGwjWRnjbKB", data_list)
print(data_list)
