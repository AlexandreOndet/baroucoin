from __future__ import annotations # Allows for using class type hinting within class (see https://stackoverflow.com/a/33533514)
import hashlib as h
import json

from TransactionStore import *

class Block:
    def __init__(self, timestamp, transactionStore: TransactionStore, height, consensusAlgorithm: bool,
                 previousHash, miner, reward, nonce=0):
        self.timestamp = timestamp
        self.transactionStore = transactionStore
        self.height = height  # height in the blockchain, each new blocks increments it
        self.consensusAlgorithm = consensusAlgorithm  # False = Proof of work, True = Proof of stake
        self.previousHash = previousHash
        self.miner = miner
        self.reward = reward
        self.nonce = nonce
    
    def __str__(self):
        return json.dumps(self.__dict__, sort_keys=True)

    def __repr__(self):
        return json.dumps(self.__dict__, sort_keys=True)

    def __eq__(self, other):
        return self.getHash() == other.getHash()

    def getHash(self):
        return h.sha3_256(self.toJSON().encode()).hexdigest()

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    @classmethod
    def fromJSON(cls, block: dict) -> Block:
        return cls(**block)
