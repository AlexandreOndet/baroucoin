from ConsensusAlgorithm import *


class ProofOfWork(ConsensusAlgorithm, dict):
    def __init__(self, blockDifficulty):
        super(ProofOfWork, self).__init__()
        self.blockDifficulty = blockDifficulty

    def mine(self, block):
        isCorrect = False
        while not isCorrect:
            if block.getHash()[0:self.blockDifficulty] == '0' * self.blockDifficulty:
                isCorrect = True
                return block.nonce
            block.nonce = block.nonce + 1
