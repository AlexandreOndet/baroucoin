import time

from Block import *
from TransactionStore import *


class Blockchain:
    def __init__(self):
        self.unconfirmedTransactions = []
        self.blockChain = []

    def createGenesisBlock(self):
        genesisBlock = Block(time.time(), TransactionStore(), 0, False, "0", "0", 100)

        genesisBlock.hash = genesisBlock.getHash()
        self.blockChain.append(genesisBlock)

    @property
    def lastBlock(self):
        return self.blockChain[-1]
