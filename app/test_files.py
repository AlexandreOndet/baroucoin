import unittest
import time
from pathlib import Path

from Block import *
from Blockchain import *

class FilesTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.blockchain = Blockchain()
        self.json_filename = 'blockchain.json.temp' # Change file extension to prevent accidentaly messing with a real blockchain JSON file
        block_generator = self._generate_block(self, self.blockchain.lastBlock)

        for _ in range(20): # Add a few blocks to the blockchain
            self.blockchain.addBlock(next(block_generator))

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
                f"JSON 'blocks' data not the same length as original blockchain : original={len(self.blockchain.blockChain)}, json={len(json_data['blocks'])}")
            last_updated = json_data['savedTime']

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
            f"wont_save blockchain is longer than the original blockchain : wont_save={len(wont_save.blockChain)}, original={len(self.blockchain.blockChain)}")
        
        wont_save.saveToJSON(self.json_filename) # Overwrite is false but since the last block height is less than the last saved block height, the save won't be changed
        same_as_last_update = json.loads(Path(self.json_filename).read_text())['savedTime'] # Reload 'saveTime' from file
        self.assertEqual(last_updated, same_as_last_update, 
            f"File should not get updated : last_updated={last_updated}, same_as_previous_update={same_as_last_update}")

        wont_save.saveToJSON(self.json_filename, overwrite=True) # Force the save
        new_update = json.loads(Path(self.json_filename).read_text())['savedTime'] # Reload 'saveTime' from file, should be updated
        self.assertLess(last_updated, new_update,
            f"File did not update with overwrite=True : last_updated={last_updated}, new_update={new_update}")

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

if __name__ == '__main__':
    unittest.main(verbosity=2)