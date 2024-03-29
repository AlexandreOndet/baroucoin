import hashlib as h
import logging
import json
import socketserver
import sys
import time
from enum import Enum, auto, unique
from threading import Thread
from typing import Tuple

from app.Block import *
from app.Blockchain import *
from app.ProofOfWork import *
from app.ProofOfStake import *
from app.TCPClient import *
from app.TCPHandler import *
from app.Transaction import *
from app.TransactionStore import *
from app.Wallet import *

@unique
class SyncState(Enum):
    """Enum for specifying the sync status of a node."""
    WAITING = auto()
    FULLY_SYNCED = auto()
    ALREADY_SYNCED = auto()
    INVALID_STATE = auto()
    INVALID_PEER = auto()
    NOT_ENOUGH_HEIGHTS_RECEIVED = auto()

class FullNode(socketserver.ThreadingTCPServer):
    """Represents a full node in the network. 
    
    Peers' requests are handled by spawning a new instance of 'TCPHandler' in its own thread, calling its 'handle' function.
    'RPC_' prefixed methods are called in response to peers requests. 
    
    See https://docs.python.org/3/library/socketserver.html#module-socketserver for reference.
    """

    daemon_threads = True  # Stops server from blocking on abrupt shutdown
    allow_reuse_address = True

    def __init__(self, consensusAlgorithm: bool, existing_wallet: Wallet, 
                 difficulty=1,
                 server_address: Tuple[str, int] = ('127.0.0.1', 13337),
                 RequestHandlerClass: socketserver.BaseRequestHandler = TCPHandler):
        # Initialize the TCP server for handling peer requests
        super(socketserver.ThreadingTCPServer, self).__init__(server_address, RequestHandlerClass, bind_and_activate=False)
        
        """Manually initialize the server to fix a Linux bug preventing the reuse of a socket address even with allow_reuse_address = True.

        For some unknown reason, the implementation of socketserver.py downloaded from Python's website (https://www.python.org/downloads/source/) 
        is different from the CPython github repo (https://github.com/python/cpython) implementation which sets both SO_REUSEADDR and SO_REUSEPORT
        in order to reuse sockets (see https://github.com/python/cpython/blob/d8c07f8cb4eebbe4ed0f76ba98024313f76a181c/Lib/socketserver.py#L468-L47 and
        compare to your local Python source e.g. /usr/local/lib/python3.10/socketserver.py). 
        
        Hence, we do the same as the Github implementation, setting the sockopt manually and calling bind/activate.
        """
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"): # Will only trigger on Linux
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server_bind()
        self.server_activate()

        self.blockchain = Blockchain()
        self.client = TCPClient(server_addr=server_address)  # Create the TCPClient to interact with other peers
        self.hardSync = True
        self.isMining = False
        self.max_sync_attempts = 2
        self.peers_server = {} # Key: (HOST, PORT) of a FullNode client socket / Value: (HOST, PORT) of a Fullnode server socket
        self.syncBlockHeightReceivedFromPeer = {} # Stores the heights received from each peers for the sync process
        self.syncWaitForAllPeersThread = None
        self.synced = SyncState.FULLY_SYNCED # Consider initial nodes fully synced
        self.transaction_pool = []
        self.wallet = existing_wallet
        
        # consensusAlgorithm is True if the node is running PoS, False if it's running PoW
        self.consensusAlgorithm = ProofOfWork(difficulty) if not consensusAlgorithm else ProofOfStake(difficulty, self.wallet)
        self.blockchain.createGenesisBlock(self.isPoS())

    def server_close(self):
        """Overwrite TCPServer implementation for cleaning up on server shutdown."""
        self.client.broadcast({'end': {'server_address': self.server_address}})  # Informs other peers to close the connection
        self.shutdown()
        self.socket.close()
        self.stopMining()

    def _requireSynced(not_synced_return_value=None):
        """Define a decorator for functions that requires a synced node before being runned.
        
        It will neutralize the function call and issue a warning if the node is not synced.
        Otherwise it will execute the function call.
        """

        def _(func):
            def wrapper_func(self, *args, **kwargs):
                def issue_warning(self, *args, **kwargs):
                    self._log(logging.warning, f"Call to '{func.__name__}' requires a synced node")
                    return not_synced_return_value

                f = func
                if not(self.isNodeSynced()):
                    f = issue_warning

                return f(self, *args, **kwargs)
            return wrapper_func
        return _

    def _log(self, level_func: Callable, msg: str):
        level_func(f"N:[{self.id}] " + msg)

    def _mine(self):
        """Threaded code for continous mining of a new block."""
        self.isMining = True
        while self.isMining:
            new_block = self.createNewBlock()
            try:
                found = self.consensusAlgorithm.mine(new_block)
                if found:
                    # Clear transaction pool even if block gets later invalidated by the network (transactions will be lost in this block)
                    self.transaction_pool = []
                    self.blockchain.addBlock(new_block)
                    self.updateBalance()
                    self.client.broadcast({"newBlock": new_block.toJSON()})
            except ValueError: # Raised for PoS when node balance is insufficient 
                self.isMining = False

    @property
    def id(self) -> str:
        return self.wallet.address[:6]

    def isPoW(self) -> bool:
        return type(self.consensusAlgorithm).__name__ == "ProofOfWork"

    def isPoS(self) -> bool:
        return type(self.consensusAlgorithm).__name__ == "ProofOfStake"

    def addToTransactionPool(self, t: Transaction):
        """Add a transaction to the transaction pool that will be picked up on the next block creation from this node (no update on the current mined block)."""
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
            consensusAlgorithm=self.isPoS(),
            previousHash=previous_block.getHash(),
            miner=self.wallet.address,
            reward=self.computeReward())

    def computeReward(self) -> int:
        return 1 # TODO : Compute reward, maybe according to consensus algorithm or external rules ?

    def updateBalance(self):
        """Update the node's balance and starts mining if PoS and node is not already mining."""
        self.wallet.balance = self.blockchain.getBalance(self.wallet.address)
        if self.isPoS() and not self.isMining:
            self.startMining()

    @_requireSynced()
    def startMining(self):
        """Start the node's mining thread. 
        
        Will be called directly for starting nodes and through 'syncWithPeers' for new joining nodes.
        """
        
        if not self.isMining:
            if self.isPoS() and self.wallet.balance == 0: # Don't start mining if balance is zero for PoS
                self._log(logging.warning, "Can't start PoS mining with null balance")
                return
            self.miningThread = Thread(target=self._mine)
            self.miningThread.start()

    def stopMining(self):
        if self.isMining:
            self.isMining = False
            self.consensusAlgorithm.stopMining() # Stop current block mining
            self.miningThread.join() # Wait for mining thread to end

    @_requireSynced(not_synced_return_value=False)
    def validateTransaction(self, check_t: Transaction) -> bool:
        """Validate a transaction by comparing UTXO ins and outs.

        See https://github.com/bitcoinbook/bitcoinbook/blob/develop/ch10.asciidoc#independent-verification-of-transactions for reference.
        """
        
        if not (any(check_t.senders)
                and any(check_t.receivers)
                and len(check_t.senders) == len(set(check_t.senders))):  # Check for duplicate inputs
            return False

        for (addr, amount) in check_t.senders:
            # getBalance() will traverse the entire blockchain for checking the transactions (see implementation in Blockchain.py) 
            sender_balance = self.blockchain.getBalance(addr)
            if amount > sender_balance:
                return False

        return True

    @_requireSynced(not_synced_return_value=False)
    def validateNewBlock(self, newBlock: Block) -> bool:
        """Validate a new block received from the network (block attributes and transactions are checked).

        PoW: see https://github.com/bitcoinbook/bitcoinbook/blob/develop/ch10.asciidoc#validating-a-new-block for reference.
        """
        if ((len(self.blockchain.blockChain) and newBlock.height <= self.blockchain.currentHeight)
                or newBlock.previousHash != self.blockchain.lastBlock.getHash()
                or newBlock.timestamp - time.time() > 3600  # Prevent block from being too much in the future (1h max)
                or newBlock.reward != self.computeReward()):
            return False

        if self.isPoW(): # Check the new block hash according to PoW consensus rules (number of zeroes and ones)
            frac, whole = modf(self.consensusAlgorithm.blockDifficulty)
            whole = int(whole)
            if frac == 0:
                if newBlock.getHash()[0:whole] != '0' * whole:
                    return False
            elif frac == 0.5:
                if newBlock.getHash()[0:whole + 1] != '0' * whole + '1' and newBlock.getHash()[0:whole + 1] != '0' * (whole + 1):
                    return False
        elif self.isPoS(): # Check the new block nonce according to PoS consensus rules
            to_hash = newBlock.previousHash.encode() + newBlock.miner.encode() + newBlock.nonce.to_bytes(8, 'big')
            if int.from_bytes(h.sha3_256(to_hash).digest(), 'big') > int(2**256 * self.blockchain.getBalance(newBlock.miner) * self.consensusAlgorithm.blockDifficulty):
                return False

        return all([self.validateTransaction(t) for t in newBlock.transactionStore.transactions])  # Validate each transaction in the block

    def isNodeSynced(self) -> bool:
        return self.synced == SyncState.FULLY_SYNCED or self.synced == SyncState.ALREADY_SYNCED

    def syncWithPeers(self, autostart_mining=True, hard_sync=False):
        """Starts the syncing process.
        
        It consists of four steps:
        - The node sends a 'getLastBlock' RPC request to all its peers to get information about the highest chain.
        - The peers responds with a 'listLastBlocks' RPC request to the node. It will wait until all peers have responded or timeout after 3 seconds.
        - If enough responses have been received (more than half of peers), the node will ask the peer with the highest chain for the missing blocks or full blockchain (if hard_sync is True).
        - The chosen peer will then send an 'updateInventory' RPC request to the node who will update its blockchain. 
        """
        
        def _waitSyncLoop():
            while self.synced == SyncState.WAITING:
                pass

        self.stopMining()

        attempt = 1
        self.hardSync = hard_sync
        self.synced = SyncState.WAITING
        self.syncWaitForAllPeersThread = None
        
        while attempt <= self.max_sync_attempts and not self.isNodeSynced():
            self._log(logging.info, f"Starting sync with peers (attempt {attempt}/{self.max_sync_attempts})...")

            self.syncBlockHeightReceivedFromPeer = {k: 0 for k in self.peers_server.keys()}
            self.client.broadcast({
                "getLastBlock": {"latestBlockHeight": self.blockchain.currentHeight}
            })

            wait_sync_loop_thread = Thread(target=_waitSyncLoop)
            wait_sync_loop_thread.start()
            wait_sync_loop_thread.join(timeout=15)

            if wait_sync_loop_thread.is_alive(): # 15 seconds timeout reached
                self._log(logging.warning, f"Timeout for syncing node reached")

            attempt += 1
            
        if not(self.isNodeSynced()):
            self._log(logging.error, f"Could not sync node: maximum sync attempts reached ({self.max_sync_attempts}/{self.max_sync_attempts})")
        elif autostart_mining: # Node is now synced, start automining if enabled
            self.startMining()

        self.syncWaitForAllPeersThread = None

    @_requireSynced(not_synced_return_value=True)
    def RPC_getLastBlock(self, data, client_addr) -> bool:
        """Ask a peer for its blockchain's latest block height."""
        peer = self.peers_server[client_addr]
        lastBlockHeight = self.blockchain.currentHeight

        self._log(logging.debug, f"Received 'getLastBlock' request from {peer} with data : {data}")
        if (data["latestBlockHeight"] <= lastBlockHeight):
            data = {'listLastBlocks': {'lastBlockHeight': lastBlockHeight}}
            
            self._log(logging.debug, f"Sending block height {lastBlockHeight} to {peer}")
            self.client.send_data_to_peer(data, peer) # TODO : check return data

        return True

    def RPC_listLastBlocks(self, data, client_addr) -> bool:
        """Waits for receiving block heights from all peers."""
        def _syncWaitForAllPeers():
            while (len(self.syncBlockHeightReceivedFromPeer) != len(self.peers_server.keys())): # Try to get data from all peers
                pass

        peer = self.peers_server[client_addr]
        self.syncBlockHeightReceivedFromPeer[client_addr] = data['lastBlockHeight']
        self._log(logging.debug, f"Received block height {data['lastBlockHeight']} from {peer}")
        
        if not self.syncWaitForAllPeersThread:
            self.syncWaitForAllPeersThread = Thread(target=_syncWaitForAllPeers)
            self.syncWaitForAllPeersThread.start()
        else:
            return True # Run this RPC only once and wait for thread to finish or timeout

        self.syncWaitForAllPeersThread.join(timeout=3)
        if (len(self.syncBlockHeightReceivedFromPeer) < len(self.peers_server.keys())//2): # If less than half of peers responded, abort sync
            self.synced = SyncState.NOT_ENOUGH_HEIGHTS_RECEIVED
            self._log(logging.error, 
                f"Could not sync node, not enough data received from peers: received={len(self.syncBlockHeightReceivedFromPeer)} < required={len(self.peers_server.keys())//2}")
            return True

        self._log(logging.debug, f"Got {len(self.syncBlockHeightReceivedFromPeer)} block heights from peers: {self.syncBlockHeightReceivedFromPeer}")

        if (self.hardSync): # Reset blockchain state in case of hard sync
            self.blockchain.blockChain = []
            self.blockchain.createGenesisBlock()

        # Getting peer with highest returned block height and storing both the address and block height received for checking in updateInventory request
        self.chosen_peer = max(self.syncBlockHeightReceivedFromPeer, key=self.syncBlockHeightReceivedFromPeer.get)
        self.sync_height = self.syncBlockHeightReceivedFromPeer[self.chosen_peer]
        peer = self.peers_server[self.chosen_peer]

        if (self.sync_height > self.blockchain.currentHeight):
            self._log(logging.debug, f"Sending 'getInventory' request to {peer}")
            self.client.send_data_to_peer({
                'getInventory': {
                    'fromHeight': self.blockchain.currentHeight,
                    'toHeight': self.sync_height
                }
            }, peer)
        else: # If maximum received height is same or less than current blockchain height, node is synced
            self.synced = SyncState.ALREADY_SYNCED
            self._log(logging.warning, f"Blockchain is already synced at highest block height")

        return True

    @_requireSynced(not_synced_return_value=True)
    def RPC_getInventory(self, data, client_addr) -> bool:
        """Ask a peer for certains blocks."""
        peer = self.peers_server[client_addr]
        from_height = data['fromHeight']
        to_height = data['toHeight']

        self._log(logging.debug, f"Received 'getInventory' request from {peer} with data : {data}")
        if (from_height > to_height):
            self._log(logging.error, f"Malformed inventory request: from_height > to_height")
        elif (to_height > 0 and to_height <= self.blockchain.currentHeight):
            data = {'updateInventory': []}
            for block in self.blockchain.blockChain[from_height:to_height+1]: # +1 for index offset
                data['updateInventory'].append(block.toJSON())

            self._log(logging.debug, f"Sending inventory to {peer}")
            self.client.send_data_to_peer(data, peer)

        return True

    def RPC_updateInventory(self, data, client_addr) -> bool:
        """Update the node's blockchain for blocks received by a chosen peer."""
        if (client_addr == self.chosen_peer): # Peer verification
            blocks = data
            required_blocks = self.sync_height - self.blockchain.currentHeight + 1 # +1 for height index offset
            if (len(blocks) == required_blocks):
                original_chain = [b for b in self.blockchain.blockChain]
                if self.hardSync:
                    self.blockchain.blockChain = []
                    
                for json_block in [json.loads(b) for b in blocks]:
                    json_block['transactionStore'] = TransactionStore.fromJSON(json_block['transactionStore'])
                    block = Block.fromJSON(json_block)

                    """Skip blockchain validation allowing for dynamic difficulty change and faster node syncying (not the best way...)."""
                    # if not(self.validateNewBlock(block)):
                    # 	self._log(logging.error, 
                    # 		f"Could not update inventory, blockchain is invalid for block {block.height}: last_block_hash={self.blockchain.lastBlock.getHash()}, new_block_previous_hash={block.previousHash}")
                    # 	break

                    self.blockchain.addBlock(block)

                if (self.blockchain.currentHeight != self.sync_height):
                    self.synced = SyncState.INVALID_STATE
                    self.blockchain.blockChain = original_chain # Restore original chain
                else:
                    self.synced = SyncState.FULLY_SYNCED
                    self._log(logging.info,
                        f"Finished syncing blockchain state from block {original_chain[-1].height} to block {self.sync_height} (chosen_peer={self.chosen_peer}) [success]")
            elif (required_blocks == 0):
                self.synced = SyncState.ALREADY_SYNCED
                self._log(logging.warning, 
                    f"Blockchain state is already updated from {client_addr}")
            else:
                self.synced = SyncState.INVALID_STATE
                self._log(logging.warning, 
                    f"Received 'updateInventory' request with wrong number of blocks: len_block={len(blocks)}, required_blocks={required_blocks}")
        else:
            self.synced = SyncState.INVALID_PEER
            self._log(logging.warning, 
                f"Received 'updateInventory' request from non-chosen peer: client_addr={client_addr}")

        return True

    def RPC_connect(self, data, client_addr) -> bool:
        """Connect back to a peer."""
        server_address = tuple(data['server_address'])
        self.peers_server[client_addr] = server_address
        if (self.client.connect(server_address)):
            self._log(logging.info, f"Connected back to {server_address} [success]")
        else:
            self._log(logging.warning, f"Already connected to {server_address}")

        return True

    @_requireSynced(not_synced_return_value=True)
    def RPC_newBlock(self, data, client_addr) -> bool:
        """Validates a new block received from the network."""
        data = json.loads(data)
        data['transactionStore'] = TransactionStore.fromJSON(data['transactionStore']);
        block = Block.fromJSON(data)
        peer = self.peers_server[client_addr]
        self._log(logging.debug, f"Received 'newBlock' request from {peer} with data : {data}")
        if (self.validateNewBlock(block)):
            self.consensusAlgorithm.stopMining() # Stop mining for this block and start mining next one
            self.blockchain.addBlock(block)
            self._log(logging.info, f"Validated block #{block.height} from {peer} (hash: {block.getHash()}) [success]")
            self.updateBalance()
        else:
            self._log(logging.warning,
                      f"Block #{block.height} from {peer} is invalid: hash={block.getHash()}, currentHeight={self.blockchain.currentHeight}")
        return True

    def RPC_end(self, data, client_addr) -> bool:
        """Terminates a peer's connection."""
        server_address = tuple(data['server_address'])
        self._log(logging.debug, f"Received disconnect request from {server_address}")
        self.client.disconnect(server_address, True)  # Disconnects and remove the peer from the peers list

        return False