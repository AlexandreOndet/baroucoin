from app.ConsensusAlgorithm import *
from app.TreeLeaf import *


class ProofOfStake(ConsensusAlgorithm, dict):
    def __init__(self, blockDifficulty):
        super(ProofOfStake, self).__init__()
        # TODO build the tree
        self.rootNode = TreeLeaf()

    def mine(self, block):

        pass

    def pickTheWinner(self, number):
        return self.pickTheWinnerRecursive(number, self.rootNode)

    def pickTheWinnerRecursive(self, number, node: TreeLeaf):
        if node.leftChild is None and node.rightChild is None:
            return node.value
        elif node.rightChild is None:
            return self.pickTheWinnerRecursive(self, number, node.leftChild)  # if there's only one child
        elif node.leftChild.number > number:
            return self.pickTheWinnerRecursive(self, number, node.leftChild)
        else:
            return self.pickTheWinnerRecursive(self, number, node.rightChild)
