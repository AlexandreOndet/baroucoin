import requests
import os
import json

def get_public_ip():
    return requests.get('https://api.ipify.org').text


def get_all_peers() -> dict:
    with open(os.environ['PEERS_JSON_PATH'], "r") as f:
        peers = json.loads(f.read())
    return peers
