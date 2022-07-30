from app.ConsensusAlgorithm import *


class ProofOfStake(ConsensusAlgorithm, dict):
    def __init__(self, blockDifficulty):
        super(ProofOfStake, self).__init__()

    def mine(self, block):
        pass
