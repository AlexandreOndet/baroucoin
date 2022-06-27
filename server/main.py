from typing import Set, Dict, Any
import os
from fastapi import FastAPI, Request
import json
import time
import requests

blockchain = FastAPI()
PEERS_JSON_PATH = os.getcwd() + "/peers.json"


def get_public_ip():
    return requests.get('https://api.ipify.org').text




@blockchain.get("/test")
def test_hello_word():
    return {"Barou": "COIN ! "}


@blockchain.get("/")
async def index():
    """
    Index endpoint for Blockchain server.
    :return: str
    """
    return "Index"


@blockchain.get("/mainchain")
async def b_chain() -> dict:
    """
    Ledger endpoint for Blockchain server. Returns the current state of the blockchain.
    :return: dict -> keys: chain:Lis[dict] -> Serialized Blocks
    """
    blocks = []  # TODO implement the necessary logic to fetch current state of blockchain
    return {"current_chain": blocks}


@blockchain.get("/peers")
async def peers() -> dict[str, Any]:
    """
    Peers List endpoint for Blockchain Server.
    :return: dict -> keys: peers: List[str]
    """
    with open(PEERS_JSON_PATH, "r+") as f:
        peers = json.loads(f.read())
        # ips = [peer.ip for peer in peers.keys()]
        return {"peers": peers}


@blockchain.get("/new-peer")
async def new_peer(request: Request) -> dict:
    """
    Adds a new peer to the blockchain network
    :return: dict -> keys: new_peer:str -> IP Address
    """
    server_address = get_public_ip()
    peer_host = request.client.host
    peer_port = request.client.port
    if peer_host == "127.0.0.1":
        address = f"{server_address}"
    else:
        address = f"http://{peer_host}:{peer_port}"
    print(address)
    with open(PEERS_JSON_PATH, "r") as f:
        data = json.loads(f.read())
    if address in data:
        return {"Following address is already registered as a node": address}
    data[address] = {time.asctime()}
    with open(PEERS_JSON_PATH, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return {"registeredFrom": address, "peers": data}
