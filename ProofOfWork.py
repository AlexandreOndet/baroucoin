import ConcensusAlgorithm

class ProofOfWork(ConcensusAlgorithm):
    def __init__(self, blockDifficulty):
        self.blockDifficulty = blockDifficulty
