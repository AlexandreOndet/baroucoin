import logging
import time
import json
import os
from typing import Union

from Block import *
from TransactionStore import *

class Blockchain:
    def __init__(self):
        self.blockChain = []
        self.createGenesisBlock()

    def __str__(self):
        return str(self.blockChain)

    def __repr__(self):
        return str(self.blockChain)

    def createGenesisBlock(self):
        genesisBlock = Block(0, TransactionStore(), 0, False, "0", "0", 100)

        self.blockChain.append(genesisBlock)

    @property
    def lastBlock(self):
        return self.blockChain[-1]

    def addBlock(self, block: Block):
        self.blockChain.append(block)

    def loadFromJSON(self, file: Union[str, bytes], overwrite=False) -> bool:
        lastSavedBlockHeight = self.lastBlock.height
        lastUpdated = "?"
        countUpdated = 0
        try:
            with open(file) as f:
                try:
                    data = json.load(f)
                    if overwrite:
                        self.blockChain = []
                        lastSavedBlockHeight = -1
                    elif (data['lastBlockHeight'] <= self.lastBlock.height):
                        logging.info("Loading aborted: current blockchain is longer than previously saved blockchain (set overwrite=True to force load) [failure]")
                        return False

                    for block in data['blocks']:
                        block = json.loads(block)
                        if (block['height'] > lastSavedBlockHeight):
                            self.blockChain.append(Block.fromJSON(block))
                            countUpdated += 1

                    lastUpdated = data['savedTime']
                except Exception as e:
                    logging.error(f"Could not load save file: {e}")
                    return False
        except FileNotFoundError:
            logging.error(f"File '{file}' does not exists !")
            return False
        except Exception as e:
            logging.error(f"Exception caught : {e}")
            return False

        logging.info(f"Successfully loaded {countUpdated} blocks from '{file}' (last updated {lastUpdated}) [success]")
        return True

    def saveToJSON(self, file: Union[str, bytes], overwrite=False) -> bool:
        blockchain = {} # JSON object to save blockchain data
        lastSavedBlockHeight = -1 # Allow inclusion of genesis block with height=0
        if (os.path.dirname(file)): # Create directory for file if needed
            os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, 'a+') as f: # 'a+' enables reading AND writing to file AND create it if it does not yet exists
            blockchain['blocks'] = []

            if not overwrite:
                f.seek(0) # Go back to start of file since it's opened in 'append' mode
                try:
                    data = json.loads(f.read())
                    if (data['lastBlockHeight'] > self.lastBlock.height):
                        logging.info("Saving aborted: previously saved blockchain is longer than current blockchain (set overwrite=True to force save) [failure]")
                        return False

                    # Add previously saved blocks to the new save file
                    lastSavedBlockHeight = data['lastBlockHeight']
                    previousBlocks = data['blocks']
                    for block in previousBlocks:
                        blockchain['blocks'].append(json.loads(block))
                except FileNotFoundError:
                    logging.warning(f"File not found, creating new file...")
                except Exception as e:
                    logging.error(f"Exception caught : {e}")
                    return False

            for block in self.blockChain:
                if (block.height > lastSavedBlockHeight):
                    blockchain['blocks'].append(block.toJSON())

            blockchain['savedTime'] = time.time()
            blockchain['lastBlockHeight'] = self.lastBlock.height

            f.truncate(0) # Erase file content
            f.write(json.dumps(blockchain))

        logging.info(f"Successfully saved {len(self.blockChain)} blocks to '{file}' [success]")
        return True