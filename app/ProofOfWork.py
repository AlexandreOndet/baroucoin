from app.ConsensusAlgorithm import *
from math import modf


class ProofOfWork(ConsensusAlgorithm, dict):
    def __init__(self, blockDifficulty):
        super(ProofOfWork, self).__init__()
        self.blockDifficulty = blockDifficulty

    def mine(self, block):
        frac, whole = modf(self.blockDifficulty)
        whole = int(whole)
        self.alreadyFound = False
        if frac == 0:
            while not self.alreadyFound and block.getHash()[0:self.blockDifficulty] != '0' * self.blockDifficulty:
                block.nonce = block.nonce + 1

            return not self.alreadyFound  # True if node found the block and False if others found it
        elif frac == 0.5:
            while not self.alreadyFound and (block.getHash()[0:whole + 1] != '0' * whole + '1' and block.getHash()[0:whole + 1] != '0' * (whole + 1)):
                block.nonce = block.nonce + 1

            return not self.alreadyFound  # True if node found the block and False if others found it
        else:
            raise ValueError("blockDIfficulty must be an integer or a float with a decimal part equals to 0.5")

    def stopMining(self):
        self.alreadyFound = True
