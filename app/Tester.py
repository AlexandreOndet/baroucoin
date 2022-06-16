import unittest
from ProofOfWork import *
from Blockchain import *


class MyTestCase(unittest.TestCase):
    def test_amount_of_zeros(self):
        chain = Blockchain()
        chain.createGenesisBlock()
        PoW = ProofOfWork(1)
        print("Nonce="+str(PoW.mine(chain.lastBlock)))
        print("Hash="+chain.lastBlock.getHash())
        self.assertEqual(chain.lastBlock.getHash()[0:PoW.blockDifficulty], '0'*PoW.blockDifficulty)  # add assertion here


if __name__ == '__main__':
    unittest.main()


