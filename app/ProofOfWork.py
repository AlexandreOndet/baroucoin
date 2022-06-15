from ConsensusAlgorithm import *

class ProofOfWork(ConsensusAlgorithm, dict):
    def __init__(self, blockDifficulty):
        super(ProofOfWork, self).__init__()
        self.blockDifficulty = blockDifficulty
