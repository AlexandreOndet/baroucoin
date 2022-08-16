from app.ConsensusAlgorithm import *
from math import modf

class ProofOfWork(ConsensusAlgorithm, dict):
    """Proof of Work consensus based on the number of leading zeros and ones for adjusting the mining difficulty."""
    def __init__(self, blockDifficulty):
        super(ProofOfWork, self).__init__()
        self.blockDifficulty = blockDifficulty

    def mine(self, block):
        """Increases the block nonce until a suitable hash is found.
        
        Run in a thread by the FullNode.
        If the difficulty is a whole number, the hash must contains a given number of leading zeroes.
        Else the hash must contains the whole part of leadings zeroes plus an additional '1' or '0' 
        """
        
        frac, whole = modf(self.blockDifficulty)
        if frac != 0 and frac != 0.5 or whole < 0:
            raise ValueError("blockDifficulty must be a positive integer or float with a decimal part equal to 0.5")

        whole = int(whole)
        self.alreadyFound = False

        while not self.alreadyFound and (block.getHash()[0:whole] != '0' * whole or (not block.getHash()[whole] in ['0', '1'] if frac else False)):
            block.nonce += 1

        return not self.alreadyFound

    def stopMining(self):
        self.alreadyFound = True
