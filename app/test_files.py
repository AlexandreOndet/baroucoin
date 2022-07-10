import unittest
import time
from pathlib import Path

from Block import *
from Blockchain import *

class FilesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.blockchain = Blockchain()
        cls.json_filename = 'blockchain.json.temp' # Change file extension to prevent accidentaly messing with a real blockchain JSON file
        cls.block_generator = cls._generate_block(cls, cls.blockchain.lastBlock)

        for _ in range(20): # Add a few blocks to the blockchain
            cls.blockchain.addBlock(next(cls.block_generator))
        assert len(cls.blockchain.blockChain) == 21, f"Blockchain did not initialize correctly : expected 21 blocks got {len(cls.blockchain.blockChain)}"

    '''
        Verifies saving blockchain to JSON 
    '''
    def test_blockchain_save_json(self):
        self.blockchain.saveToJSON(self.json_filename, overwrite=True)
        self.assertTrue(Path(self.json_filename).is_file(), 
            f"File was not created : json_filename={self.json_filename}")
        
        savefile_keys = ['savedTime', 'lastBlockHeight', 'blocks']
        with open(self.json_filename) as f:
            json_data = json.loads(f.read())
            self.assertTrue(all([key in json_data for key in savefile_keys]), 
                f"Malformed JSON one (or all) of {savefile_keys} keys not found : json_data={json_data}")
            self.assertEqual(len(self.blockchain.blockChain), len(json_data['blocks']), 
                f"Saved blockchain is not the same length as original blockchain : original={len(self.blockchain.blockChain)}, json={len(json_data['blocks'])}")
            last_updated = json_data['savedTime']

        time.sleep(0.01) # Add delay before updating so saved timestamp are not equal
        self.blockchain.addBlock(next(self.block_generator))
        self.blockchain.saveToJSON(self.json_filename) # No overwrite, file should be updated

        with open(self.json_filename) as f:
            json_data = json.loads(f.read())
            self.assertLess(last_updated, json_data['savedTime'],
                f"File did not get updated : last_updated={last_updated}, savedTime={json_data['savedTime']}")
            self.assertEqual(len(self.blockchain.blockChain), len(json_data['blocks']), 
                f"Saved blockchain is not the same length as updated blockchain : updated={len(self.blockchain.blockChain)}, json={len(json_data['blocks'])}")

    '''
        Verifies a shorter blockchain is not saved without setting overwrite=True
    '''
    def test_blockchain_save_json_height_check(self):
        self.blockchain.saveToJSON(self.json_filename, overwrite=True)
        last_updated = json.loads(Path(self.json_filename).read_text())['savedTime']
        
        wont_save = Blockchain()
        wont_save_block_generator = self._generate_block(wont_save.lastBlock)

        for _ in range(10): # Generate fewer blocks than the original blockchain
            wont_save.addBlock(next(wont_save_block_generator))

        self.assertLess(len(wont_save.blockChain), len(self.blockchain.blockChain), 
            f"'wont_save' blockchain is longer than the original blockchain : wont_save={len(wont_save.blockChain)}, original={len(self.blockchain.blockChain)}")
        
        wont_save.saveToJSON(self.json_filename) # Overwrite is false but since the last block height is less than the last saved block height, the save won't be updated
        same_as_last_update = json.loads(Path(self.json_filename).read_text())['savedTime'] # Reload 'saveTime' from file
        self.assertEqual(last_updated, same_as_last_update, 
            f"File should not get updated : last_updated={last_updated}, same_as_previous_update={same_as_last_update}")

        time.sleep(0.01) # Add delay before updating so saved timestamp are not equal
        wont_save.saveToJSON(self.json_filename, overwrite=True) # Force the save
        new_update = json.loads(Path(self.json_filename).read_text())['savedTime'] # Reload 'saveTime' from file, should be updated
        self.assertLess(last_updated, new_update,
            f"File did not update with overwrite=True : last_updated={last_updated}, new_update={new_update}")

    def test_blockchain_load_json(self):
        self.blockchain.saveToJSON(self.json_filename, overwrite=True)

        copy = Blockchain()
        copy.loadFromJSON(self.json_filename)

        self.assertEqual(len(copy.blockChain), len(self.blockchain.blockChain),
            f"'copy' blockchain length is not the same as original : copy={len(copy.blockChain)}, original={len(self.blockchain.blockChain)}")

        divergent_index = self._check_blockchain_equality(copy, self.blockchain)
        self.assertEqual(divergent_index, len(copy.blockChain),
                f"'copy' blockchain data is not the same as original : block_height={divergent_index}")

    def tearDown(self):
        Path(self.json_filename).unlink() # Delete file after each test

    def _generate_block(self, startingBlock: Block) -> Block:
        lastBlock = startingBlock
        while True:
            block = Block(
                timestamp=time.time(), 
                transactionStore=TransactionStore(), 
                height=lastBlock.height + 1,
                consensusAlgorithm=True, 
                previousHash=lastBlock.getHash(), 
                miner=0,
                reward=0, 
                nonce=0
            )
            yield block
            lastBlock = block

    '''
        Returns index of deviation (block different in the two blockchains).
        Equal => i == len(chain_a) == len(chain_b) 
        Not Equal => i == 0 or i == index of divergent block 
    '''
    def _check_blockchain_equality(self, a : Blockchain, b : Blockchain) -> int:
        i = 0
        chain_a, chain_b = (a.blockChain, b.blockChain)
        if (len(chain_a) != len(chain_b)):
            return 0

        while (i < len(chain_a) and chain_a[i] == chain_b[i]):
            i += 1

        return i

if __name__ == '__main__':
    unittest.main(verbosity=2)