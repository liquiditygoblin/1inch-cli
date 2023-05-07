import json
from os import listdir
from os.path import isfile, join
import requests


def open_json(file):
    with open(file) as f:
        return json.load(f)


def find_token_in_files(chain_id, symbol):
    symbol = symbol.upper()

    token_list_path = f"config/token_lists/{chain_id}/"
    token_list_files = [f for f in listdir(token_list_path) if isfile(join(token_list_path, f))]

    for file in token_list_files:
        json_data = open_json(f"{token_list_path}{file}")

        potential_tokens = []
        
        for t in json_data["tokens"]:
            if t["symbol"].upper() == symbol:

                # Some files like uniswap.json contain tokens for multiple chains
                # so it's not enough to simpy check the symbol matches, but we 
                # also need to check the chainId is the same

                if "chainId" not in t:
                    potential_tokens.append(t)
                
                # if chainId is present in token, we want to check if before adding it to list
                else:
                    if int(t["chainId"]) == chain_id:
                        potential_tokens.append(t)

        if len(potential_tokens) == 0:
            continue
        elif len(potential_tokens) > 1:
            # TODO: handle multiple tokens with same symbol
            return potential_tokens[0]
        else:
            return potential_tokens[0]

    return None

