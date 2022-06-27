import os
from typing import Any

from fastapi import FastAPI, Request
import json
import os

from app.Blockchain import Blockchain

blockchain = Blockchain()
fullNode = FastAPI()
PEERS_JSON_PATH = os.getcwd() + "/node_neighbors.json"


@fullNode.get("/")
def test_hello_word():
    return {"I'm a client at ip": "#TODO Add local ip"}


@fullNode.get("/getLastBlock")
async def lastBlockHash() -> dict:
    """
    Returns last known block hash.
    :return: dict -> keys: chain:Lis[dict] -> Serialized Blocks
    """
    lastBlock = ""  # TODO add logic for last known block
    return {"The known tip of the chain is : ": lastBlock}


@fullNode.get("/inv")
async def last_500_blocks() -> list:
    # TODO Replace boiler plate code bellow with real blockchain call
    return [blockchain[i] for i in range(len(blockchain), len(blockchain) - 500, -1)]


@fullNode.get("/getData/{block_hash}")
async def getBlockData(block_hash):
    # TODO Replace boiler plate code bellow with real blockchain call
    return blockchain[block_hash]
