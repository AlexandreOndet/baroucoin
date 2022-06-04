import ConsensusAlgorithm


class ProofOfWork(ConsensusAlgorithm):
    def __init__(self, blockDifficulty):
        self.blockDifficulty = blockDifficulty
