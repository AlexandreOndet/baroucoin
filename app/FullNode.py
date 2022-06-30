import time
import socketserver
import sys
from typing import Tuple
import json

from Block import *
from Blockchain import *
from ProofOfWork import *
from TCPClient import *
from TCPHandler import *
from Transaction import *
from TransactionStore import *
from Wallet import *

'''
    See https://docs.python.org/3/library/socketserver.html#module-socketserver for reference. 
    Requests are handled by spawning a new instance of 'TCPHandler' in its own thread, calling its 'handle' function.
'''


class FullNode(socketserver.ThreadingTCPServer):
    """docstring for FullNode"""
    daemon_threads = True  # Stops server from blocking on abrupt shutdown
    allow_reuse_address = True

    def __init__(self, consensusAlgorithm: bool, existing_wallet: Wallet,
                 server_address: Tuple[str, int] = ('localhost', 13337),
                 RequestHandlerClass: socketserver.BaseRequestHandler = TCPHandler):
        socketserver.ThreadingTCPServer.__init__(self, server_address,
                                                 RequestHandlerClass)  # Initialize the TCP server for handling peer requests
        self.wallet = existing_wallet
        self.consensusAlgorithm = ProofOfWork(
            1) if not consensusAlgorithm else None  # TODO : Change to ProofOfStake and set difficulty accordingly
        self.client = TCPClient(server_addr=server_address)  # Create the TCPClient to interact with other peers
        self.blockchain = Blockchain()  # TODO : ask peers for blockchain state
        self.transaction_pool = []
        self.initTransactionPool()

    def __del__(self):
        self.server_close()

    def initTransactionPool(self):
        f = open('transaction_loop.json')
        data = json.load(f)
        for i in data['transactions']:
            self.transaction_pool.append(Transaction(list(i['senders']), list(i['receivers'])))
        f.close()

    def addToTransactionPool(self, t: Transaction):
        self.transaction_pool.append(t)

    def createNewBlock(self) -> Block:
        previous_block = self.blockchain.lastBlock
        return Block(
            timestamp=time.time(),
            transactionStore=TransactionStore(self.transaction_pool[previous_block.height % len(self.transaction_pool)]),
            # each time, we pick the next transaction in the pool
            height=previous_block.height + 1,
            consensusAlgorithm=False,
            previousHash=previous_block.getHash(),
            miner=self.wallet.address,
            reward=self.computeReward())

    def computeReward(self) -> int:
        return 1  # TODO : Compute reward, maybe according to consensus algorithm or external rules ?

    def mineNewBlock(
            self):  # TODO : rework to be able to interrupt mining once a valid block has been received for the same height
        new_block = self.createNewBlock()
        self.consensusAlgorithm.mine(new_block)
        self.blockchain.addBlock(new_block)
        self.client.broadcast({"newBlock": new_block.toJSON()})

    '''
        See https://github.com/bitcoinbook/bitcoinbook/blob/develop/ch10.asciidoc#independent-verification-of-transactions for reference
    '''

    def validateTransaction(self, t: Transaction) -> bool:
        if not (any(t.senders)
                and any(t.receivers)
                and len(t.senders) == len(set(t.senders))):  # Check for duplicate inputs
            return False

        for (addr, amount) in t.senders:
            exists = False
            spent = False
            for block in self.blockchain.blockChain:
                for k in block.transactionStore.transactions:
                    if addr in [r_addr for (r_addr, _) in k.receivers]:
                        exists = True
                    if addr in [s_addr for (s_addr, _) in k.senders]:
                        spent = True
            if not exists or spent:
                return False

        return True

    '''
        See https://github.com/bitcoinbook/bitcoinbook/blob/develop/ch10.asciidoc#validating-a-new-block for reference
    '''

    def validateNewBlock(self, newBlock: Block) -> bool:
        if ((len(self.blockchain.blockChain) and newBlock.height <= self.blockchain.lastBlock.height)
                or newBlock.previousHash != self.blockchain.lastBlock.getHash()
                or newBlock.getHash()[
                   0:self.consensusAlgorithm.blockDifficulty] != '0' * self.consensusAlgorithm.blockDifficulty
                or newBlock.timestamp - time.time() > 3600  # Prevent block from being too much in the future (1h max)
                or newBlock.reward != self.computeReward()):
            return False

        return all(
            [self.validateTransaction(t) for t in newBlock.transactionStore.transactions])  # Validate each transaction
