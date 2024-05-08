# convert a csv dictionary to a json dictionary
# input: csv dictionary
# output: json dictionary

import json
import os

IN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'synonyms.csv')
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'synonyms.json')

json_dict = {}

with open(IN_FILE, 'r') as f:
    for line in f:
        line = line.strip()
        if line == '':
            continue
        # get strings before and after the comma
        key, _, value = line.partition(',')

        value = value.strip("\"")
        value_delimiter = "," if "," in line else ";"
        value = [x.strip() for x in value.split(value_delimiter) if len(x.split(" ")) <= 3]
        if len(value) > 0:
            json_dict[key] = value

bidirectional_dict = {}
for key, value in json_dict.items():
    for synonym in value:
        value_copy = value.copy()
        value_copy.remove(synonym)
        value_copy.append(key)
        bidirectional_dict[synonym] = value_copy

json_dict.update(bidirectional_dict)
with open(OUT_FILE, 'w') as f:
    json.dump(json_dict, f)
