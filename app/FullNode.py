import time

from Block import *
from Blockchain import *
from Wallet import *
from Transaction import *
from TransactionStore import *
from ProofOfWork import *


class FullNode(object):
    """docstring for FullNode"""

    def __init__(self, consensusAlgorithm: bool, existing_wallet: Wallet):
        super(FullNode, self).__init__()
        self.wallet = existing_wallet
        self.consensusAlgorithm = ProofOfWork(
            1) if not consensusAlgorithm else None  # TODO : Change to ProofOfStake and set difficulty accordingly
        self.transaction_pool = []
        self.blockchain = Blockchain()  # Should the FullNode class search for existing blockchain or should the constructor of Blockchain do it ?

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
        return 1  # TODO : Compute reward, maybe according to consensus algorithm or external rules ?*

    def mineNewBlock(self):
        self.consensusAlgorithm.mine(self.createNewBlock())

    '''
        See https://github.com/bitcoinbook/bitcoinbook/blob/develop/ch10.asciidoc#independent-verification-of-transactions for reference
    '''

    def validateTransaction(self, t: Transaction) -> bool:
        if not (any(t.senders)
                and any(t.receivers)
                and len(t.senders) == len(set(t.senders))):
            return False

        for i in t.senders:
            exists = False
            spent = False
            print(t)
            for j in self.blockchain.blockChain:
                print(j.transactionStore)
                for k in j.transactionStore.transactions:
                    if i in k.receivers:
                        exists = True
                    if i in k.senders:
                        print(k)
                        spent = True
            if not exists or spent:
                print(f"exists={exists} et spent={spent}")
                return False

        return True  # Check for duplicate inputs

    '''
        See https://github.com/bitcoinbook/bitcoinbook/blob/develop/ch10.asciidoc#validating-a-new-block for reference
    '''

    def validateNewBlock(self, newBlock: Block) -> bool:
        if (newBlock.getHash()[
            0:self.consensusAlgorithm.blockDifficulty] != '0' * self.consensusAlgorithm.blockDifficulty
                or newBlock.timestamp - time.time() > 3600  # Prevent block from being too much in the future (1h max)
                or newBlock.reward != self.computeReward()):
            return False

        return all(
            [self.validateTransaction(t) for t in newBlock.transactionStore.transactions])  # Validate each transaction

# node = FullNode(None, Wallet("test"))
# print(vars(node.createNewBlock()))
