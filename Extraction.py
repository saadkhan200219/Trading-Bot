import json
import csv
import os

def jsonl_to_csv(directory, csv_file):
    with open(csv_file, 'w', newline='') as f_csv:
        csv_writer = csv.writer(f_csv)
        file_count = 0
        for filename in os.listdir(directory):
            if(file_count > 5):
                break
            if filename.endswith('.jsonl'):
                jsonl_file = os.path.join(directory, filename)
                with open(jsonl_file, 'r') as f_jsonl:
                    first_line = f_jsonl.readline()
                    first_json = json.loads(first_line)
                    header = list(first_json['d'].keys())
                    if(file_count == 0):
                        csv_writer.writerow(header)
                    
                    for line in f_jsonl:
                        json_data = json.loads(line)
                        csv_writer.writerow(list(json_data['d'].values()))
                file_count = file_count + 1

directory = 'D:\EaseBot\Data\Raw'
csv_file = 'crypto_data_sub.csv'
jsonl_to_csv(directory, csv_file)
print(f"Conversion from JSONL to CSV completed. Output saved to '{csv_file}'.")