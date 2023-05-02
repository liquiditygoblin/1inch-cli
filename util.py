import json


def open_json(file):
    with open(file) as f:
        return json.load(f)
