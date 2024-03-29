from math import modf
import time
import unittest
import warnings

from app.ProofOfWork import *
from app.Blockchain import *
from app.FullNode import *
from app.Transaction import *


class PoWTests(unittest.TestCase):
    @classmethod
    def setUpClass(self): # Called before running any test functions
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning) # Clear the unclosed sockets warning for tests

    def test_difficulty_whole(self):
        chain = Blockchain()
        chain.createGenesisBlock()
        
        PoW = ProofOfWork(1)
        PoW.mine(chain.lastBlock)
        self.assertEqual(chain.lastBlock.getHash()[0:PoW.blockDifficulty], '0' * PoW.blockDifficulty,
                         f"PoW whole difficulty broken : hash={chain.lastBlock.getHash()}, difficulty={PoW.blockDifficulty}")

    def test_difficulty_frac(self):
        chain = Blockchain()
        chain.createGenesisBlock()

        PoW = ProofOfWork(1.5)
        PoW.mine(chain.lastBlock)
        
        frac, whole = modf(PoW.blockDifficulty)
        whole = int(whole)
        self.assertTrue(chain.lastBlock.getHash()[0:whole + 1] == '0' * (whole + 1) or chain.lastBlock.getHash()[0:whole + 1] == '0' * whole + '1',
                        f"PoW frac difficulty broken : hash={chain.lastBlock.getHash()}, difficulty={PoW.blockDifficulty}")

    def test_difficulty_invalid(self):
        chain = Blockchain()
        chain.createGenesisBlock()

        PoW = ProofOfWork(-1)
        with self.assertRaises(ValueError):
            PoW.mine(chain.lastBlock)

        PoW = ProofOfWork(1.2)
        with self.assertRaises(ValueError):
            PoW.mine(chain.lastBlock)

    def test_block_validation_difficulty(self):
        node = FullNode(consensusAlgorithm=False, existing_wallet=Wallet(""))
        block = Block(timestamp=time.time(), transactionStore=TransactionStore(), height=1,
                      consensusAlgorithm=node.consensusAlgorithm, previousHash=node.blockchain.lastBlock.getHash(), miner=0, reward=node.computeReward(),
                      nonce=0)

        while block.getHash()[0] == '0':  # Generate a block with hash not validating any Proof of Work (no zeroes at start)
            block = Block(timestamp=time.time(), transactionStore=TransactionStore(), height=1,
                          consensusAlgorithm=node.consensusAlgorithm, previousHash=node.blockchain.lastBlock.getHash(), miner=0,
                          reward=node.computeReward(), nonce=0)
        self.assertFalse(node.validateNewBlock(block),
                         f"Non-mined block passes as valid block : hash={block.getHash()}, difficulty={node.consensusAlgorithm.blockDifficulty}")

        node.consensusAlgorithm.mine(block)  # Genuine mined block will pass the test
        self.assertTrue(node.validateNewBlock(block),
                        f"Mined block is not validated : hash={block.getHash()}, difficulty={node.consensusAlgorithm.blockDifficulty}")

    def test_block_validation_timestamp(self):
        node = FullNode(consensusAlgorithm=False, existing_wallet=Wallet(""))

        # Timestamp 1 day in the future
        invalid_block = Block(timestamp=time.time() + 24 * 3600, transactionStore=TransactionStore(), height=1,
                              consensusAlgorithm=node.consensusAlgorithm, previousHash=node.blockchain.lastBlock.getHash(), miner=0,
                              reward=node.computeReward(), nonce=0)
        node.consensusAlgorithm.mine(invalid_block)  # Don't forget to mine the block for valid hash
        self.assertFalse(node.validateNewBlock(invalid_block),
                         f"Invalid timestamp for block passes as valid block : timestamp={invalid_block.timestamp}, diff={invalid_block.timestamp - time.time()}")

        # Correct timestamp
        valid_block = Block(timestamp=time.time(), transactionStore=TransactionStore(), height=1,
                            consensusAlgorithm=node.consensusAlgorithm, previousHash=node.blockchain.lastBlock.getHash(), miner=0,
                            reward=node.computeReward(), nonce=0)
        node.consensusAlgorithm.mine(valid_block)  # Don't forget to mine the block for valid hash
        self.assertTrue(node.validateNewBlock(valid_block),
                        f"Correct timestamp for block is not validated : timestamp={valid_block.timestamp}, diff={valid_block.timestamp - time.time()}")

    def test_block_validation_reward(self):
        node = FullNode(consensusAlgorithm=False, existing_wallet=Wallet(""))

        # Invalid null reward
        invalid_block = Block(timestamp=time.time(), transactionStore=TransactionStore(), height=1,
                              consensusAlgorithm=node.consensusAlgorithm, previousHash=node.blockchain.lastBlock.getHash(), miner=0, reward=0, nonce=0)
        node.consensusAlgorithm.mine(invalid_block)  # Don't forget to mine the block for valid hash
        self.assertFalse(node.validateNewBlock(invalid_block),
                         f"Invalid reward for block passes as valid block : reward={invalid_block.reward}, computed={node.computeReward()}")

        # Correct reward
        valid_block = Block(timestamp=time.time(), transactionStore=TransactionStore(), height=1,
                            consensusAlgorithm=node.consensusAlgorithm, previousHash=node.blockchain.lastBlock.getHash(), miner=0,
                            reward=node.computeReward(), nonce=0)
        node.consensusAlgorithm.mine(valid_block)  # Don't forget to mine the block for valid hash
        self.assertTrue(node.validateNewBlock(valid_block),
                        f"Correct reward for block is not validated : reward={valid_block.reward}, computed={node.computeReward()}")

    def test_block_validation_transactions(self):
        node = self._init_node_with_transaction()
        block = Block(timestamp=time.time(), transactionStore=TransactionStore(), height=2,
                      consensusAlgorithm=node.consensusAlgorithm, previousHash=node.blockchain.lastBlock.getHash(), miner=0, reward=node.computeReward(),
                      nonce=0)

        # Generate valid transaction
        valid_transaction = Transaction(senders=[(Wallet("first").address, 1)],
                                        receivers=[(Wallet("second").address, 1)])
        block.transactionStore.addTransaction(valid_transaction)
        node.consensusAlgorithm.mine(block)  # Don't forget to mine the block for valid hash
        self.assertTrue(node.validateNewBlock(block),
                        f"Correct transactions for block are not validated : transactions={block.transactionStore.transactions}")

        # Generate invalid empty transaction
        invalid_transaction = Transaction(senders=[], receivers=[])
        block.transactionStore.addTransaction(invalid_transaction)
        node.consensusAlgorithm.mine(block)  # Don't forget to mine the block for valid hash
        self.assertFalse(node.validateNewBlock(block),
                         f"Invalid transaction for block gets validated : transactions={block.transactionStore.transactions}")

    def test_transaction_validation(self):
        node = self._init_node_with_transaction()
        self.assertFalse(node.validateTransaction(Transaction(senders=[], receivers=[])),
                         "Empty transactions gets validated")
        self.assertFalse(node.validateTransaction(Transaction(senders=[(Wallet("first").address, 1)], receivers=[])),
                         "Empty receivers gets validated")
        # self.assertFalse(node.validateTransaction(Transaction(senders=[], receivers=[(Wallet("second").address, 1)]))) not possible as it raises ValueError in the current implementation
        self.assertFalse(node.validateTransaction(
            Transaction(senders=[(Wallet("first").address, 1), (Wallet("first").address, 1)],
                        receivers=[(Wallet("second").address, 1)])), "Duplicated senders gets validated")

        self.assertTrue(node.validateTransaction(
            Transaction(senders=[(Wallet("first").address, 1)], receivers=[(Wallet("second").address, 1)])),
            "Correct transaction gets invalidated")

    def test_transaction_pool(self):
        transactions = [
            Transaction(senders=[(Wallet("1").address, 1)], receivers=[(Wallet("2").address, 1)]),
            Transaction(senders=[(Wallet("2").address, 1)], receivers=[(Wallet("3").address, 1)]),
            Transaction(senders=[(Wallet("3").address, 1)], receivers=[(Wallet("1").address, 1)])
        ]
        node = FullNode(consensusAlgorithm=False, existing_wallet=Wallet(""))

        for t in transactions:
            node.addToTransactionPool(t)
        self.assertEqual(node.transaction_pool, transactions,
            f"Node transaction pool doesn't contains all transactions : transaction_pool={node.transaction_pool}, transactions={transactions}")

        b = node.createNewBlock()
        self.assertEqual(b.transactionStore.transactions, transactions, 
            f"New block transactions are not the same as original transactions : newblock={b.transactionStore}, original={transactions}")

        node.removeFromTransactionPool(transactions[0])
        self.assertEqual(node.transaction_pool, transactions[1:],
            f"Transaction is not removed from transaction pool : transaction_pool={node.transaction_pool}, new_transactions={transactions[1:]}")

    def _init_node_with_transaction(self):
        node = FullNode(consensusAlgorithm=False, existing_wallet=Wallet(""))
        t = Transaction(senders=[(Wallet("beforefirst").address, 1)], receivers=[(Wallet("first").address, 1)])
        b = Block(timestamp=time.time(), transactionStore=TransactionStore(), height=1,
                  consensusAlgorithm=node.consensusAlgorithm, previousHash=node.blockchain.lastBlock.getHash(), miner=0, reward=node.computeReward(),
                  nonce=0)
        b.transactionStore.addTransaction(t)
        node.consensusAlgorithm.mine(b)
        node.blockchain.addBlock(b)  # set up a transaction to have a valid output later
        return node

if __name__ == '__main__':
    unittest.main(verbosity=2)
