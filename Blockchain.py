import time

from Block import *
from ProofOfWork import *
from TransactionStore import *


class Blockchain:
    def __init__(self):
        self.unconfirmedTransactions = []
        self.blockChain = []
        self.createGenesisBlock()

    def createGenesisBlock(self):
        genesisBlock = Block(time.time(), TransactionStore(), 0, ProofOfWork(1), "0", "0",100)
        # for now consensus
        # alg is a string because it's not implemented yet
        genesisBlock.hash = genesisBlock.getHash()
        self.blockChain.append(genesisBlock)

    @property
    def lastBlock(self):
        return self.blockChain[-1]
