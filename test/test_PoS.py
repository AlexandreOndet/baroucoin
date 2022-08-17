import hashlib as h
import time
import unittest
import warnings

from app.ProofOfStake import *
from app.Blockchain import *
from app.FullNode import *
from app.Transaction import *

class PoSTests(unittest.TestCase):
    @classmethod
    def setUpClass(self): # Called before running any test functions
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning) # Clear the unclosed sockets warning for tests

    def test_difficulty(self):
        wallet = Wallet("test_PoS")
        wallet.balance = 1

        chain = Blockchain()
        chain.createGenesisBlock(True)
        
        PoS = ProofOfStake(10, wallet)
        PoS.mine(chain.lastBlock)

        to_hash = chain.lastBlock.previousHash.encode() + wallet.address.encode() + chain.lastBlock.nonce.to_bytes(8, 'big')
        _hash = int.from_bytes(h.sha3_256(to_hash).digest(), 'big')
        threshold = int(2**256 * wallet.balance * PoS.blockDifficulty)
        
        self.assertLessEqual(_hash, threshold, f"Incorrect hash for PoS:\nhash={_hash}\nthreshold={threshold}")

    def test_balance_from_transactions(self):
        w_alice = Wallet("Alice")
        w_bob = Wallet("Bob")
        
        blockchain = Blockchain()
        blockchain.createGenesisBlock(True, beneficiaries=[w_alice.address, w_alice.address]) # Alice's wallet gets two coins at the start
        w_alice.balance = 2

        t = Transaction(senders=[(w_alice.address, 2)], receivers=[(w_bob.address, 2)]) # Send two coins to Bob
        b = Block(timestamp=time.time(), transactionStore=TransactionStore([t]), height=1,
                  consensusAlgorithm=True, previousHash=blockchain.lastBlock.getHash(), miner=w_alice.address, reward=100) # Alice gets 100 coins as mining reward
        
        PoS = ProofOfStake(10, w_alice)
        if PoS.mine(b):
            blockchain.addBlock(b)

        w_alice.balance = blockchain.getBalance(w_alice.address)
        w_bob.balance = blockchain.getBalance(w_bob.address)
        
        self.assertEqual(w_alice.balance, 100, f"Wrong balance for Alice: expected 100 got {w_alice.balance} coins")
        self.assertEqual(w_bob.balance, 2, f"Wrong balance for Bob: expected 2 got {w_bob.balance} coins")

    def test_block_validation(self):
        w_alice = Wallet("Alice")
        w_bob = Wallet("Bob")
        
        blockchain = Blockchain()
        blockchain.createGenesisBlock(True, beneficiaries=[w_alice.address, w_alice.address]) # Alice's wallet gets two coins at the start
        w_alice.balance = 2

        node_alice = FullNode(consensusAlgorithm=True, existing_wallet=w_alice)
        node_alice.blockchain.blockChain[0] = blockchain.blockChain[0]
        block = node_alice.createNewBlock()
        if node_alice.consensusAlgorithm.mine(block):
            node_alice.blockchain.addBlock(block)

        node_bob = FullNode(consensusAlgorithm=True, existing_wallet=w_bob)
        node_bob.blockchain.blockChain[0] = blockchain.blockChain[0]

        self.assertTrue(node_bob.validateNewBlock(node_alice.blockchain.lastBlock), f"Bob could not validate Alice's new block")

if __name__ == '__main__':
    unittest.main(verbosity=2)
