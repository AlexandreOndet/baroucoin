import logging
import random
from threading import Thread

from app.FullNode import *
from app.ChartsRenderer import *

class Orchestrator(Thread):
    """
    Represents the simulation as a threaded class. 
    The simulation runs until explicit shutdown through user input. 
    Parameters of the simulation can be edited in the __init__ method.

    Attributes:
    - startingNodes: number of peers at the start of simulation
    - maxNodes: maximum numbers of peers allowed
    - epochTime: speed of the simulations for triggering events
    - miningDifficulty: float value in 0.5 increments representing the mining difficulty for PoW

    Random events:
    - transactionFrequency: chances for a transaction to be sent to a random peer
    - disconnectFrequency: chances for a peer to leave the network
    - newPeerFrequency: chances for a new peer to join the network
    """

    def __init__(self, renderer: ChartsRenderer):
        super(Orchestrator, self).__init__()

        self.setup()
        self.isRunning = True
        self.isPaused = False
        self.transactions = self._getNextTransaction()
        self.nodes = []
        self.renderer = renderer

    def _pause(f):
        """Decorator for pausing the simulation and resuming after the function's execution."""
        def make_pause(self, *args):
            self.isPaused = True # Pause the simulation
            f(self, *args)
            self.isPaused = False # Unpause the simulation
        return make_pause

    def _wrap_parameters(self) -> dict:
        """Wraps simulation parameters and state in a dict for use by the rendering process."""
        d = dict()
        d['startingNodes'] = self.startingNodes
        d['maxNodes'] = self.maxNodes
        d['epochTime'] = self.epochTime
        d['isRunning'] = self.isRunning
        d['miningDifficulty'] = self.miningDifficulty
        d['transactionFrequency'] = self.transactionFrequency
        d['disconnectFrequency'] = self.disconnectFrequency
        d['newPeerFrequency'] = self.newPeerFrequency
        d['nodes'] = self.nodes

        return d

    def _roll(self, threshold: float) -> bool:
        """Generate a random number between 1 and 100 (included) and return True if below or equal threshold (must be percentage value)."""
        return random.randint(1, 100) <= 10*threshold

    def _setupNodes(self):
        self.nodes = [
            FullNode(
                consensusAlgorithm=False,
                difficulty=self.miningDifficulty, 
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

    @_pause
    def _updateDifficulty(self):
        for node in self.nodes:
            node.stopMining()

        for node in self.nodes:
            node.consensusAlgorithm.blockDifficulty = self.miningDifficulty

        for node in self.nodes:
            node.startMining()

        self._log(logging.info, f"New difficulty set to {self.miningDifficulty}")

    def _getNextTransaction(self):
        """Generator for transactions: loads transactions from JSON and loops through the list sequentially."""
        i = 0
        while True:
            yield Transaction(senders=[(Wallet(str(hex(i))).address, 1)],
                              receivers=[(Wallet(str(hex(i + 1))).address, 1)])
            i += 1

    def _log(self, level_func: Callable, msg: str):
        level_func(f"M:[_MAIN_] " + msg)
        self.renderer.log(level_func.__name__, msg)

    @property
    def numberOfNodes(self) -> int:
        return len(self.nodes)

    def setup(self, startingNodes=3, maxNodes=5, epochTime=1000, miningDifficulty=5, transactionFrequency=.5, disconnectFrequency=.1, newPeerFrequency=.2):
        self.startingNodes = startingNodes
        self.maxNodes = maxNodes
        self.epochTime = epochTime  # in milliseconds, control speed of the simulation
        self.miningDifficulty = miningDifficulty

        assert self.maxNodes >= self.startingNodes
        
        self.transactionFrequency = transactionFrequency
        self.disconnectFrequency = disconnectFrequency
        self.newPeerFrequency = newPeerFrequency
    
    @st.cache( # Streamlit cache used for faster rendering of real-time data
        hash_funcs={
            '_thread.lock': id, 
            '_io.TextIOWrapper': id, 
            'builtins.generator': id, 
            '_thread.RLock': id, 
            'builtins.weakref': id,
        },
        suppress_st_warning=True
    )
    def run(self):
        self._setupNodes()
        self.renderer.render(self._wrap_parameters()) # First rendering pass loads the charts faster

        while self.isRunning:
            while self.isPaused:
                pass

            if (self._roll(self.disconnectFrequency) and self.numberOfNodes > 1):
                chosenNode = random.choice(self.nodes)
                self.removeNode(chosenNode)

            if (self._roll(self.newPeerFrequency)):
                self.addNewNode()

            if (self._roll(self.transactionFrequency)):
                chosenNode = random.choice(self.nodes)
                chosenNode.addToTransactionPool(next(self.transactions))
                self._log(logging.info, f"Sending transaction to {chosenNode.id}...")

            self.renderer.render(self._wrap_parameters())
            time.sleep(self.epochTime / 1_000)

        for node in self.nodes:
            node.server_close()  # Stops the node's server

    def stop(self):
        self.isRunning = False

    def addNewNode(self) -> bool:
        if (self.numberOfNodes == self.maxNodes):
            self._log(logging.warning, f"Maximum numbers of nodes reached ({self.numberOfNodes}/{self.maxNodes} nodes)")
            return False # TODO : Use exceptions instead

        self._log(logging.info, f"Adding new peer to network...")
        new_node = FullNode(
            consensusAlgorithm=False,
            difficulty=self.miningDifficulty,
            existing_wallet=Wallet(str(self.numberOfNodes)),
            server_address=("127.0.0.1", 10000 + self.numberOfNodes) # TODO: handle invalid/busy socket
        )
        self.nodes.append(new_node)
        Thread(target=new_node.serve_forever).start()
        
        for peer in self.nodes[:-1]:
            new_node.client.connect(peer.server_address)

        new_node.syncWithPeers()

        self._log(logging.info, f"New peer {new_node.id} joined the network ({self.numberOfNodes}/{self.maxNodes} nodes) [success]")
        return True

    def removeNode(self, node: FullNode):
        node.server_close()  # Stops the node's server
        self.nodes.remove(node)
        self._log(logging.info, f"Peer {node.id} is leaving the network ({self.numberOfNodes}/{self.maxNodes} nodes)")

    def removeLastNode(self):
        self.removeNode(self.nodes[-1])

    @_pause
    def syncAllNodes(self):
        self._log(logging.info, "Syncing nodes...")

        for node in self.nodes:
            node.stopMining()

        for node in self.nodes: # Make all nodes sync before mining again, resetting any forks 
            node.syncWithPeers(autostart_mining=False, hard_sync=True)

        for node in self.nodes:
            node.startMining()

        self._log(logging.info, "Syncing finished [success]")

    def increaseDifficulty(self):
        self.miningDifficulty += 0.5
        self._updateDifficulty()

    def decreaseDifficulty(self):
        self.miningDifficulty -= 0.5
        self._updateDifficulty()