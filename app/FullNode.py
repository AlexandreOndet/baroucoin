import time

from Block import *
from Blockchain import *
from Wallet import *
from Transaction import *
from TransactionStore import *
from ConsensusAlgorithm import *
import hashlib as h

class FullNode(object):
    """docstring for FullNode"""
    def __init__(self, consensusAlgorithm: ConsensusAlgorithm, existing_wallet: Wallet):
        super(FullNode, self).__init__()
        self.wallet = existing_wallet
        self.consensusAlgorithm = consensusAlgorithm
        self.transaction_pool = []
        self.blockchain = Blockchain() # Should the FullNode class search for existing blockchain or should the constructor of Blockchain do it ?

    def addToTransactionPool(self, t: Transaction):
        self.transaction_pool.append(t)

    def createNewBlock(self) -> Block:
        previous_block = self.blockchain.lastBlock
        return Block(
            timestamp=time.time(), 
            transactionStore=TransactionStore(self.transaction_pool), 
            height=previous_block.height + 1, 
            consensusAlgorithm=self.consensusAlgorithm,
            previousHash=previous_block.getHash(),
            miner=self.wallet.address,
            reward=self.computeReward())

    def computeReward(self) -> int:
        return 1 # TODO : Compute reward, maybe according to consensus algorithm or external rules ?*

    def mineNewBlock(self):
        self.consensusAlgorithm.mine(self.createNewBlock())

    def getLastBlockHash(self):
        return h.sha3_256(self.blockchain.lastBlock).hexdigest()

# node = FullNode(None, Wallet("test"))
# print(vars(node.createNewBlock()))