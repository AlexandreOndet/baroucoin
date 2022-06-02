import hashlib as h
from json import dumps

class Block:
    def __init__(self, timestamp, transactionStore, height, concensusAlgorithm, previousHash, miner, reward, nonce=0):
        self.timestamp=timestamp
        self.transactionStore=transactionStore
        self.height=height #height in the blockchain, each new blocks increments it
        self.concensusAlgorithm=concensusAlgorithm
        self.previousHash=previousHash
        self.miner=miner
        self.reward=reward
        self.nonce=nonce

    def getHash(self):
        block= dumps(self.__dict__, sort_keys=True)
        return h.sha3_256(block.encode()).hexdigest()