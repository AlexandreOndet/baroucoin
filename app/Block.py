import TransactionStore
import hashlib as h
from json import dumps

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
        return dumps(self.__dict__, sort_keys=True)

    def __repr__(self):
        return dumps(self.__dict__, sort_keys=True)

    def getHash(self):
        return h.sha3_256(self.toJSON().encode()).hexdigest()

    def toJSON(self):
        return dumps(self, default=lambda o: o.__dict__, sort_keys=True)
