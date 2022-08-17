from __future__ import annotations # Allows for using class type hinting within class (see https://stackoverflow.com/a/33533514)
import hashlib as h
import json

from app.TransactionStore import *

class Block:
    """Represents a blockchain block.

    :param timestamp:
    :param transactionStore: stores the list of transactions in the block
    :param height:
    :param consensusAlgorithm: stores the consensus used for the blockchain
    :param previousHash:
    :param miner: address who mined the block
    :param reward: miner's reward for mining the block
    :param nonce: used for PoW for modifying the block hash / used for PoS for storing the timestamp validating the right to mine the new block
    """
    
    def __init__(self, timestamp: float, transactionStore: TransactionStore, height: int, consensusAlgorithm: bool,
                 previousHash: str, miner: str, reward: int, nonce: int=0):
        self.timestamp = timestamp
        self.transactionStore = transactionStore
        self.height = height  # height in the blockchain, each new blocks increments it
        self.consensusAlgorithm = consensusAlgorithm  # False = Proof of work, True = Proof of stake
        self.previousHash = previousHash
        self.miner = miner
        self.reward = reward
        self.nonce = nonce
    
    def __str__(self):
        return self.toJSON()

    def __repr__(self):
        return self.toJSON()

    def __eq__(self, other):
        return self.getHash() == other.getHash()

    def getHash(self):
        return h.sha3_256(self.toJSON().encode()).hexdigest()

    def toJSON(self):
        _json = json.loads(json.dumps(self, default=lambda o: o.__dict__, sort_keys=True))
        _json['transactionStore'] = [t.toJSON() for t in self.transactionStore.transactions] if self.transactionStore.isEmpty else []

        return json.dumps(_json)

    @classmethod
    def fromJSON(cls, block: dict) -> Block:
        return cls(**block)
