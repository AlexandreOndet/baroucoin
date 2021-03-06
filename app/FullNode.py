import logging
import json
import socketserver
import sys
import time
from typing import Tuple

from app.Block import *
from app.Blockchain import *
from app.ProofOfWork import *
from app.TCPClient import *
from app.TCPHandler import *
from app.Transaction import *
from app.TransactionStore import *
from app.Wallet import *

'''
    See https://docs.python.org/3/library/socketserver.html#module-socketserver for reference. 
    Requests are handled by spawning a new instance of 'TCPHandler' in its own thread, calling its 'handle' function.
'''


class FullNode(socketserver.ThreadingTCPServer):
    """docstring for FullNode"""
    daemon_threads = True  # Stops server from blocking on abrupt shutdown
    allow_reuse_address = True

    def __init__(self, consensusAlgorithm: bool, existing_wallet: Wallet,
                 server_address: Tuple[str, int] = ('127.0.0.1', 13337),
                 RequestHandlerClass: socketserver.BaseRequestHandler = TCPHandler):
        socketserver.ThreadingTCPServer.__init__(self, server_address,
                                                 RequestHandlerClass)  # Initialize the TCP server for handling peer requests
        self.wallet = existing_wallet
        self.consensusAlgorithm = ProofOfWork(
            1) if not consensusAlgorithm else None  # TODO : Change to ProofOfStake and set difficulty accordingly
        self.client = TCPClient(server_addr=server_address)  # Create the TCPClient to interact with other peers
        self.blockchain = Blockchain()  # TODO : ask peers for blockchain state
        self.transaction_pool = []

    def sync_with_peers(self):
        latest_local_block_hash = self.blockchain.lastBlock.getHash()
        self.client.broadcast({
            "getLastBlock": json.dumps({"latestBlockHash": latest_local_block_hash})
        })

    def send_last_block(self, peer_address):
        latest_local_block = self.blockchain.lastBlock
        data = {"receiveMyLastBlock": json.dumps({"latestBlockHash": latest_local_block.getHash(),
                                                  "lastBlockHeight": latest_local_block.height})}
        #logging.debug(f"Sending last known block to {peer_address}")
        self.client.send_data_to_peer(data, peer_address)

    def ask_inventory(self, peer_address, receivedLatestBlockHash, receivedLatestBlockHeight):
        logging.debug(f"Asking {peer_address} for inventory")
        latest_local_block = self.blockchain.lastBlock
        data = {"askingForInventory": json.dumps({"from": latest_local_block.height, "to": receivedLatestBlockHeight})}
        self.client.send_data_to_peer(data, peer_address)

    def returnInventory(self, peer_address, from_height, to_height):
        logging.debug(f"Sending to {peer_address} inventory with blocks from {from_height} to {to_height} height")
        for block_height in range(from_height, to_height, 1):
            block = self.blockchain.blockChain[block_height]
            block_json = block.toJSON()
            # Sending block per block to avoid going above buffer size of recv in TCPHandler
            data = {"returnInventory": json.dumps({"block_height": block_height, "block_json": block_json})}
            self.client.send_data_to_peer(data, peer_address)

    def __del__(self):
        self.server_close()

    @property
    def id(self):
        return self.wallet.address[:6]

    def addToTransactionPool(self, t: Transaction):
        self.transaction_pool.append(t)

    def removeFromTransactionPool(self, t: Transaction):
        try:
            self.transaction_pool.remove(t)
        except ValueError:
            logging.error(f"Could not find transaction in transaction pool : {t}")

    def createNewBlock(self) -> Block:
        previous_block = self.blockchain.lastBlock
        return Block(
            timestamp=time.time(),
            transactionStore=TransactionStore([t for t in self.transaction_pool]),
            height=previous_block.height + 1,
            consensusAlgorithm=False,
            previousHash=previous_block.getHash(),
            miner=self.wallet.address,
            reward=self.computeReward())

    def computeReward(self) -> int:
        return 1  # TODO : Compute reward, maybe according to consensus algorithm or external rules ?

    def mineNewBlock(self):  # TODO : interrupt mining once a valid block has been received for the same height
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
