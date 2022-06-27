import requests
import json
import os
import FullNode
from Wallet import Wallet

PEERS_JSON_PATH = os.getcwd() + "/node_neighbors.json"
DNS_SERVER_IP = ""

client = FullNode(None, Wallet("test"))


def get_public_ip():
    return requests.get('https://api.ipify.org').text


def get_all_peers() -> dict:
    with open(PEERS_JSON_PATH, "r") as f:
        peers = json.loads(f.read())
    return peers


def fetch_peers_from_dns():
    """
    Register this client as a full node on DNS and get all peers registered to join the network
    """
    # Starts by asking a DNS server for peers list
    peers_response = requests.get(DNS_SERVER_IP + "/peers")
    print(peers_response)
    myIp = get_public_ip()
    if peers_response["registeredFrom"] == myIp:
        peers = peers_response["peers"]
        with open(PEERS_JSON_PATH, 'w') as f:
            json.dump(peers, f, ensure_ascii=False, indent=4)


def fetch_most_recents_block():
    """
    Fetch most recent blocks from all nodes on the network (spreading the work as much as possible)
    """
    peers = get_all_peers()
    for peer in peers.keys():
        lastBlockHash = requests.get(peer + "/getLastBlock")
        if lastBlockHash != client.getLastBlockHash():
            inv = requests.get(peer + "/inv")
            # TODO for all blocks that aren't currently in the client block chain, send proper message to other nodes to fetch data
