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
        self.maxNodes = 3
        self.epoch = 1000 # in milliseconds
        self.transactionFrequency = 5
        self.miningFrequency = 2
        self.isRunning = True

        self.transactions = self._getNextTransaction()
        self.nodes = [FullNode(consensusAlgorithm=False, existing_wallet=Wallet(str(i)), server_address=("127.0.0.1", 10000 + i)) for i in range(self.maxNodes)]
        
        for node in self.nodes: # Initiate server on all nodes
            Thread(target=node.serve_forever).start()
        
        for i in range(self.numberOfNodes - 1): # Make nodes all connected to each other
            node = self.nodes[i]
            for peer in self.nodes[i+1:]:
                if (node.client.connect(peer.server_address)):
                    self._log(logging.info, f"Connected {node.id} {node.server_address} to {peer.id} {peer.server_address} [success]")
                else:
                    self._log(logging.info, f"Failed to connect {node.id} {node.server_address} to {peer.id} {peer.server_address} [failure]")

    @property
    def numberOfNodes(self) -> int:
        return len(self.nodes)

    def run(self):
        while self.isRunning:
            if (random.randint(1, 10) <= self.transactionFrequency):
                chosenNode = random.choice(self.nodes)
                chosenNode.addToTransactionPool(next(self.transactions))
                self._log(logging.info, f"Sending transaction to {chosenNode.id}...")

            for node in self.nodes:
                if (random.randint(1, 10) <= self.miningFrequency):
                    node.mineNewBlock()
                    self._log(logging.info, f"Node {node.id} is mining block #{node.blockchain.lastBlock.height}")
            time.sleep(self.epoch / 1000)

        for node in self.nodes:
            node.client.broadcast({'end': node.server_address}) # Informs other peers to close the connection
            node.shutdown() # Stops the node's server

    def addNode(self) -> bool:
        if (self.numberOfNodes == self.maxNodes):
            self._log(logging.info, f"Maximum numbers of nodes reached ({self.maxNodes} nodes) [failure]")
            return False

        self.nodes.append(FullNode(consensusAlgorithm=False, existing_wallet=Wallet(str(self.numberOfNodes)), server_address=("127.0.0.1", 10000 + self.numberOfNodes)))
        return True

    def removeNode(self, node: FullNode):
        node.client.broadcast({'end': node.server_address}) # Informs other peers to close the connection
        node.shutdown() # Stops the node's server
        self.nodes.remove(node)

    '''
        Generator for transactions: loads transactions from JSON and loops through the list sequentially 
    '''
    def _getNextTransaction(self):
        transactions = []
        with open(app_dir / 'transaction_loop.json') as f:
            data = json.load(f)
            for t in data['transactions']:
                transactions.append(Transaction(list(t['senders']), list(t['receivers'])))

        i = 0
        while True:
            yield transactions[i]
            i = (i + 1) % len(transactions)

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
        while (user_input not in ['q', 'a', 'Q', 'A']):
            user_input = input()

        if (user_input == 'q' or user_input == 'Q'):
            run = False
        elif (user_input == 'a' or user_input == 'A'):
            simulation.addNode()
            logging.info(f"Added new node")

    simulation.isRunning = False
