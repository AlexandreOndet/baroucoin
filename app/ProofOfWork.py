from app.ConsensusAlgorithm import *

class ProofOfWork(ConsensusAlgorithm, dict):
    def __init__(self, blockDifficulty):
        super(ProofOfWork, self).__init__()
        self.blockDifficulty = blockDifficulty

    def mine(self, block):
        self.alreadyFound = False
        while not self.alreadyFound and block.getHash()[0:self.blockDifficulty] != '0' * self.blockDifficulty:
            block.nonce = block.nonce + 1

        return not self.alreadyFound # True if node found the block and False if others found it

    def stopMining(self):
        self.alreadyFound = True