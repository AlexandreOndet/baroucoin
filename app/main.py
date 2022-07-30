import logging
import random
from dotenv import load_dotenv
from pathlib import Path
from threading import Thread

from app.FullNode import *

load_dotenv()
app_dir = Path(__file__).parent


class Orchestrator(Thread):
    """docstring for Orchestrator"""

    def __init__(self):
        super(Orchestrator, self).__init__()
        self.startingNodes = 3
        self.maxNodes = 5
        self.epoch = 2000  # in milliseconds
        self.isRunning = True
        
        # TODO: Make easier system for setting the frequencies
        self.transactionFrequency = 5
        self.miningFrequency = 2
        self.disconnectFrequency = 1
        self.newPeerFrequency = 2

        self.transactions = self._getNextTransaction()
        self.nodes = [
            FullNode(consensusAlgorithm=False, existing_wallet=Wallet(str(i)), server_address=("127.0.0.1", 10000 + i))
            for i in range(self.startingNodes)]

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

    @property
    def numberOfNodes(self) -> int:
        return len(self.nodes)

    def run(self):
        while self.isRunning:
            # if (self._roll(1, 15, self.disconnectFrequency)):
            # 	chosenNode = random.choice(self.nodes)
            # 	self.removeNode(chosenNode)

            # if (self._roll(1, 15, self.newPeerFrequency)):
            # 	self.addNewNode()

            if (self._roll(1, 10, self.transactionFrequency)):
                chosenNode = random.choice(self.nodes)
                chosenNode.addToTransactionPool(next(self.transactions))
                self._log(logging.info, f"Sending transaction to {chosenNode.id}...")

            for node in self.nodes:
                if (self._roll(1, 10, self.miningFrequency)):
                    node.mineNewBlock()
                    self._log(logging.info, f"Node {node.id} is mining block #{node.blockchain.lastBlock.height}")
                    break # Test for only one node mining per epoch
                
            time.sleep(self.epoch / 1000)

        for node in self.nodes:
            node.client.broadcast({'end': {'server_address': node.server_address}})  # Informs other peers to close the connection
            node.shutdown()  # Stops the node's server

    def addNewNode(self) -> bool:
        if (self.numberOfNodes == self.maxNodes):
            self._log(logging.warning, f"Maximum numbers of nodes reached ({self.maxNodes} nodes)")
            return False # TODO : Use exceptions instead

        new_node = FullNode(consensusAlgorithm=False, existing_wallet=Wallet(str(self.numberOfNodes)),
                                   server_address=("127.0.0.1", 10000 + self.numberOfNodes))
        self.nodes.append(new_node)
        Thread(target=new_node.serve_forever).start()
        
        for peer in self.nodes[:-1]:
            new_node.client.connect(peer.server_address)

        new_node.syncWithPeers()

        self._log(logging.info, f"New peer {new_node.id} joined the network ({self.numberOfNodes}/{self.maxNodes} nodes)")
        return True

    def removeNode(self, node: FullNode):
        node.client.broadcast({'end': {'server_address': node.server_address}})  # Informs other peers to close the connection
        node.shutdown()  # Stops the node's server
        self.nodes.remove(node)
        self._log(logging.info, f"Peer {node.id} is leaving the network ({self.numberOfNodes}/{self.maxNodes} nodes)")

    '''
        Generate a random number between min and max and return True if below or equal threshold. 
    '''
    def _roll(self, _min, _max, threshold):
        return random.randint(_min, _max) <= threshold

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
        level_func(f"[_MAIN_] " + msg)

'''
    usage : python main.py
'''
if __name__ == "__main__":
    file_handler = logging.FileHandler(app_dir / "simulation.log", mode='w')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    logging.basicConfig(
        handlers=[file_handler, console_handler],
        level=logging.DEBUG,
        format='T+%(relativeCreated)d\t%(levelname)s %(message)s'
    )

    logging.addLevelName(logging.DEBUG, '[DEBUG]')
    logging.addLevelName(logging.INFO, '[*]')
    logging.addLevelName(logging.WARNING, '[!]')
    logging.addLevelName(logging.ERROR, '[ERROR]')
    logging.addLevelName(logging.CRITICAL, '[CRITICAL]')

    simulation = Orchestrator()
    simulation.start()

    run = True
    while run:
        user_input = ""
        while (user_input.lower() not in ['q', 'a', 'd']):
            user_input = input()

        if (user_input.lower() == 'q'):
            run = False
        elif (user_input.lower() == 'a'):
            simulation.addNewNode()
        elif (user_input.lower() == 'd'):
            simulation.removeNode(simulation.nodes[-1])

    simulation.isRunning = False
