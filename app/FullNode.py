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
        self.peers_server = {} # Key: (HOST, PORT) of FullNode client socket / Value: (HOST, PORT) of Fullnode server socket
        self.blockchain = Blockchain()
        self.transaction_pool = []

    '''
        Overwrite TCPServer implementation for cleaning up on server shutdown
    '''
    def server_close(self):
        self.client.broadcast({'end': {'server_address': self.server_address}})  # Informs other peers to close the connection
        self.shutdown()
        self.socket.close()

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
            validAmount = False
            spent = False
            for block in self.blockchain.blockChain:
                for k in block.transactionStore.transactions:
                    for (r_addr, r_amount) in k.receivers:
                        if addr == r_addr:
                            exists = True
                        if amount == r_amount:
                            validAmount = True
                    if addr in [s_addr for (s_addr, _) in k.senders]:
                        spent = True
            if not exists or spent or not validAmount:
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

    def syncWithPeers(self):
        # TODO : Start a thread for syncing and prevent mining blocks / retry sync after timeout or packet loss
        self._log(logging.info, f"Starting sync with peers...")
        self.syncBlockHeightReceivedFromPeer = {k: 0 for k in self.peers_server.keys()}
        self.client.broadcast({
            "getLastBlock": {"latestBlockHeight": self.blockchain.lastBlock.height}
        })

    def RPC_getLastBlock(self, data, client_addr):
        peer = self.peers_server[client_addr]
        lastBlockHeight = self.blockchain.lastBlock.height

        self._log(logging.debug, f"Received 'getLastBlock' request from {peer} with data : {data}")
        if (data["latestBlockHeight"] < lastBlockHeight):
            data = {'listLastBlocks': {'lastBlockHeight': lastBlockHeight}}
            
            self._log(logging.debug, f"Sending block height {lastBlockHeight} to {peer}")
            self.client.send_data_to_peer(data, peer) # TODO : check return data

        return True

    def RPC_listLastBlocks(self, data, client_addr):
        peer = self.peers_server[client_addr]
        self.syncBlockHeightReceivedFromPeer[client_addr] = data['lastBlockHeight']
        
        self._log(logging.debug, f"Received block height {data['lastBlockHeight']} from {peer}")
        if (len(self.syncBlockHeightReceivedFromPeer) == len(self.peers_server.keys())):
            self._log(logging.debug, f"Got all block heights from peers: {self.syncBlockHeightReceivedFromPeer}")

            # Getting peer with highest returned block height and storing both the address and block height received for checking in updateInventory request
            self.chosen_peer = max(self.syncBlockHeightReceivedFromPeer, key=self.syncBlockHeightReceivedFromPeer.get)
            self.sync_height = self.syncBlockHeightReceivedFromPeer[self.chosen_peer]
            peer = self.peers_server[self.chosen_peer]

            self._log(logging.debug, f"Sending 'getInventory' request to {peer}")
            self.client.send_data_to_peer({'getInventory': {'toHeight': self.sync_height}}, peer)

        return True

    def RPC_getInventory(self, data, client_addr):
        peer = self.peers_server[client_addr]
        to_height = data['toHeight']

        self._log(logging.debug, f"Received 'getInventory' request from {peer} with data : {data}")
        if (to_height > 0 and to_height <= self.blockchain.lastBlock.height):
            data = {'updateInventory': []}
            for block in self.blockchain.blockChain[1:to_height+1]: # All nodes have same genesis block so start at #1
                data['updateInventory'].append(block.toJSON())

            self._log(logging.debug, f"Sending inventory to {peer}")
            self.client.send_data_to_peer(data, peer)

        return True

    def RPC_updateInventory(self, data, client_addr):
        if (client_addr == self.chosen_peer): # Peer verification
            blocks = data
            required_blocks = self.sync_height - self.blockchain.lastBlock.height
            if (len(blocks) == required_blocks):
                original_chain = [b for b in self.blockchain.blockChain]
                for json_block in [json.loads(b) for b in blocks]:
                    json_block['transactionStore'] = TransactionStore.fromJSON(json_block['transactionStore'])
                    block = Block.fromJSON(json_block)

                    if not(self.validateNewBlock(block)):
                        self._log(logging.error, 
                            f"Could not update inventory: blockchain is invalid for block {block.height}")
                        break
                    self.blockchain.addBlock(block)

                if (self.blockchain.lastBlock.height != self.sync_height):
                    self.blockchain.blockChain = original_chain # Restore original chain
                else:
                    self._log(logging.info,
                        f"Finished syncing blockchain state from block {original_chain[-1].height} to block {self.sync_height} (chosen_peer={self.chosen_peer}) [success]")
            elif (required_blocks == 0):
                self._log(logging.warning, 
                    f"Blockchain state is already updated from {client_addr}")
            else:
                self._log(logging.warning, 
                    f"Received 'updateInventory' request with wrong number of blocks: len_block={len(blocks)}, required_blocks={required_blocks}")
        else:
            self._log(logging.warning, 
                f"Received 'updateInventory' request from non-chosen peer: client_addr={client_addr}")

        return True

    def RPC_connect(self, data, client_addr) -> bool:
        server_address = tuple(data['server_address'])
        self.peers_server[client_addr] = server_address
        if (self.client.connect(server_address)):
            self._log(logging.info, f"Connected back to {server_address} [success]")
        else:
            self._log(logging.warning, f"Already connected to {server_address}")

        self._log(logging.debug, f"New peer state: client.peers={self.client.peers}, peers_server={self.peers_server}")

        return True

    def RPC_newBlock(self, data, client_addr) -> bool:
        data = json.loads(data)
        data['transactionStore'] = TransactionStore.fromJSON(data['transactionStore']);
        block = Block.fromJSON(data)
        if (self.validateNewBlock(block)):
            self._log(logging.info, f"Validated block #{block.height} (hash: {block.getHash()}) [success]")
            self.blockchain.addBlock(block)
            for transaction in block.transactionStore:
                for sender in transaction.senders:
                    if sender[0] == self.wallet.address:
                        self.wallet.removeFromBalance(sender[1])
                for receiver in transaction.receivers:
                    if receiver[0] == self.wallet.address:
                        self.wallet.addToBalance(receiver[1])
        else:
            self._log(logging.warning,
                      f"Block #{block.height} invalid: hash={block.getHash()}, lastBlock.height={self.blockchain.lastBlock.height}")
        return True

    def RPC_end(self, data, client_addr) -> bool:
        server_address = tuple(data['server_address'])
        self._log(logging.debug, f"Received disconnect request from {server_address}")
        self.client.disconnect(server_address, True)  # Disconnects and remove the peer from the peers list
        if (client_addr in self.peers_server):
            del self.peers_server[client_addr]

        self._log(logging.debug, f"New peer state: client.peers={self.client.peers}, peers_server={self.peers_server}")
        
        return False

    def _log(self, level_func: Callable, msg: str):
        level_func(f"N:[{self.id}] " + msg)