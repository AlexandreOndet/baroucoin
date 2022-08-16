import time
import hashlib as h

from app.ConsensusAlgorithm import *
from app.TreeLeaf import *

class ProofOfStake(ConsensusAlgorithm, dict):
    """Proof of Stake consensus based on a node's balance and difficulty setting for creating a target threshold before mining a block."""
    def __init__(self, blockDifficulty, wallet):
        super(ProofOfStake, self).__init__()
        self.blockDifficulty = blockDifficulty
        self.node_wallet = wallet
        # self.rootNode = TreeLeaf() # TODO build the tree

    def _get_time_bytes(self) -> bytes:
        return int(time.time() * 10**7).to_bytes(8, 'big')

    def mine(self, block):
        """Compares a hash value updated by a timestamp to a threshold based on the node's wallet balance and a difficulty setting.

        The hash value is based on the previous block hash, the node's wallet address and a current timestamp.
        If this value is below the threshold, the node can mine the next block. 
        The greater the balance, the higher the threshold and hence, the more chances the node can mine the next blocks.
        """
        
        if (self.node_wallet.balance == 0):
            raise ValueError("Node can't mine if its balance is zero")

        self.alreadyFound = False
        base = block.previousHash.encode() + self.node_wallet.address.encode()
        threshold = int(2**256 * self.node_wallet.balance / self.blockDifficulty)

        block.nonce = self._get_time_bytes()
        trigger = int.from_bytes(h.sha3_256(base + block.nonce).digest(), 'big')
        while not self.alreadyFound and trigger > threshold:
            block.nonce = self._get_time_bytes()
            trigger = int.from_bytes(h.sha3_256(base + block.nonce).digest(), 'big')

        block.nonce = int.from_bytes(block.nonce, 'big') # Convet nonce back to int

        return not self.alreadyFound

    def stopMining(self):
        self.alreadyFound = True

    # def pickTheWinner(self, number):
    # 	return self.pickTheWinnerRecursive(number, self.rootNode)

    # def pickTheWinnerRecursive(self, number, node: TreeLeaf):
    # 	if node.leftChild is None and node.rightChild is None:
    # 		return node.value
    # 	elif node.rightChild is None:
    # 		return self.pickTheWinnerRecursive(self, number, node.leftChild)  # if there's only one child
    # 	elif node.leftChild.number > number:
    # 		return self.pickTheWinnerRecursive(self, number, node.leftChild)
    # 	else:
    # 		return self.pickTheWinnerRecursive(self, number, node.rightChild)
