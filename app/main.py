import requests
import json
import os

PEERS_JSON_PATH = os.getcwd() + "/node_neighbors.json"
DNS_SERVER_IP = ""


def get_public_ip():
    return requests.get('https://api.ipify.org').text


def join_blockchain():
    # Starts by asking a DNS server for peers list
    peers_response = requests.get(DNS_SERVER_IP + "/peers")
    print(peers_response)
    myIp = get_public_ip()
    if peers_response["registeredFrom"] == myIp:
        peers = peers_response["peers"]
        with open(PEERS_JSON_PATH, 'w') as f:
            json.dump(peers, f, ensure_ascii=False, indent=4)
