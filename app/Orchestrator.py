import logging
import random
from threading import Thread

from app.FullNode import *
from app.ChartsRenderer import *

class Orchestrator(Thread):
    """docstring for Orchestrator"""

    def __init__(self, renderer: ChartsRenderer):
        super(Orchestrator, self).__init__()
        self.renderer = renderer
        self.startingNodes = 3
        self.maxNodes = 5
        self.epoch_time = 1000  # in milliseconds, control speed of the simulation
        self.isRunning = True
        self.mining_difficulty = 5

        assert self.maxNodes >= self.startingNodes
        
        # TODO: Make easier system for setting the frequencies
        self.transactionFrequency = 5
        self.miningFrequency = 2
        self.disconnectFrequency = 1
        self.newPeerFrequency = 2

        self.transactions = self._getNextTransaction()
        self.nodes = []

    @property
    def numberOfNodes(self) -> int:
        return len(self.nodes)

    def run(self):
        start_btn_container = st.empty()
        start_btn = start_btn_container.button("Start simulation", key='1')
        if start_btn:
            start_btn = start_btn_container.button("Start simulation", disabled=True, key='2')

            self._setupNodes()
            self.renderer.render(self.nodes)
            while self.isRunning:
                if (self._roll(1, 15, self.disconnectFrequency) and self.numberOfNodes > 1):
                    chosenNode = random.choice(self.nodes)
                    self.removeNode(chosenNode)

                if (self._roll(1, 15, self.newPeerFrequency)):
                    self.addNewNode()

                if (self._roll(1, 10, self.transactionFrequency)):
                    chosenNode = random.choice(self.nodes)
                    chosenNode.addToTransactionPool(next(self.transactions))
                    self._log(logging.info, f"Sending transaction to {chosenNode.id}...")

                self.renderer.render(self.nodes)
                time.sleep(self.epoch_time / 1_000)

            for node in self.nodes:
                node.server_close()  # Stops the node's server

    def stop(self):
        self.isRunning = False

    def addNewNode(self) -> bool:
        if (self.numberOfNodes == self.maxNodes):
            self._log(logging.warning, f"Maximum numbers of nodes reached ({self.maxNodes} nodes)")
            return False # TODO : Use exceptions instead

        self._log(logging.info, f"Adding new peer to network...")
        new_node = FullNode(
            consensusAlgorithm=False,
            difficulty=self.mining_difficulty,
            existing_wallet=Wallet(str(self.numberOfNodes)),
            server_address=("127.0.0.1", 10000 + self.numberOfNodes) # TODO: handle invalid/busy socket
        )
        self.nodes.append(new_node)
        Thread(target=new_node.serve_forever).start()
        
        for peer in self.nodes[:-1]:
            new_node.client.connect(peer.server_address)

        new_node.syncWithPeers()

        self._log(logging.info, f"New peer {new_node.id} joined the network ({self.numberOfNodes}/{self.maxNodes} nodes)")
        return True

    def removeNode(self, node: FullNode):
        node.server_close()  # Stops the node's server
        self.nodes.remove(node)
        self._log(logging.info, f"Peer {node.id} is leaving the network ({self.numberOfNodes}/{self.maxNodes} nodes)")

    def removeLastNode(self):
        self.removeNode(self.nodes[-1])

    def syncAllNodes(self):
        for node in self.nodes:
            node.stopMining()

        for node in self.nodes: # Make all nodes sync before mining again, resetting any forks 
            node.syncWithPeers(autostart_mining=False, hard_sync=True)

        for node in self.nodes:
            node.startMining()

    '''
        Generate a random number between min and max and return True if below or equal threshold. 
    '''
    def _roll(self, _min, _max, threshold):
        return random.randint(_min, _max) <= threshold

    def _setupNodes(self):
        self.nodes = [
            FullNode(
                consensusAlgorithm=False,
                difficulty=self.mining_difficulty, 
                existing_wallet=Wallet(str(i)), 
                server_address=("127.0.0.1", 10000 + i)
            ) for i in range(self.startingNodes)
        ]

        for node in self.nodes:  # Initiate server on all nodes
            Thread(target=node.serve_forever).start()

        for i in range(self.numberOfNodes - 1):  # Make nodes all connected to each other
            node = self.nodes[i]
            for peer in self.nodes[i+1:]:
                if (node.client.connect(peer.server_address)):
                    self._log(logging.info,
                              f"Connected {node.id} {node.server_address} to {peer.id} {peer.server_address} [success]")
                else:
                    self._log(logging.error,
                              f"Failed to connect {node.id} {node.server_address} to {peer.id} {peer.server_address}")

        for node in self.nodes:
            node.startMining()

    '''
        Generator for transactions: loads transactions from JSON and loops through the list sequentially 
    '''
    def _getNextTransaction(self):
        i = 0
        while True:
            yield Transaction(senders=[(Wallet(str(hex(i))).address, 1)],
                              receivers=[(Wallet(str(hex(i + 1))).address, 1)])
            i += 1

    def _log(self, level_func: Callable, msg: str):
        if (level_func == logging.info):
            self.renderer.log(msg)
        level_func(f"M:[_MAIN_] " + msg)