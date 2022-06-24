import os
from typing import Any

from fastapi import FastAPI, Request
import json
import os

fullNode = FastAPI()
PEERS_JSON_PATH = os.getcwd() + "/node_neighbors.json"


@fullNode.get("/")
def test_hello_word():
    return {"I'm a client at ip": "#TODO Add local ip"}


@fullNode.get("/getBlock")
async def b_chain() -> dict:
    """
    Returns last known block hash.
    :return: dict -> keys: chain:Lis[dict] -> Serialized Blocks
    """
    lastBlock = "" #TODO add logic for last known block
    return {"The known tip of the chain is : ": lastBlock}


@fullNode.get("/peers")
async def peers() -> dict[str, Any]:
    """
    List of known neighbors
    :return: dict -> keys: peers: List[str]
    """
    with open(PEERS_JSON_PATH, "r+") as f:
        peers = json.loads(f.read())
        # ips = [peer.ip for peer in peers.keys()]
        return {"peers": peers}


@fullNode.get("/new-peer")
async def new_peer(request: Request) -> dict:
    """
    Adds a new peer to the blockchain network
    :return: dict -> keys: new_peer:str -> IP Address
    """
    server_address = "?whatsmyip?"
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
    data[address] = {}
    with open(PEERS_JSON_PATH, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return {"New peer registered with following address": address}
