import logging
import time
import json
import os
from typing import Union

from app.Block import *
from app.TransactionStore import *

class Blockchain:
    """Represents the blockchain."""
    def __init__(self):
        self.blockChain = []

    def __str__(self):
        return str(self.blockChain)

    def __repr__(self):
        return str(self.blockChain)

    def createGenesisBlock(self, consensus: bool=False, beneficiaries: list=[], initial_supply=100_000):
        if len(beneficiaries) > initial_supply:
            raise ValueError("Number of beneficiaries cannot exceed total initial supply")

        genesisBlock = Block(time.time(), TransactionStore(), 0, consensus, "0", "0", initial_supply)

        for address in beneficiaries:
            genesisBlock.transactionStore.addTransaction(Transaction(senders=[("0", 1)], receivers=[(address, 1)]))
        
        self.addBlock(genesisBlock)

    @property
    def lastBlock(self):
        return self.blockChain[-1]

    @property
    def currentHeight(self):
        return self.lastBlock.height

    def addBlock(self, block: Block):
        self.blockChain.append(block)

    def getBalance(self, address: str) -> int:
        balance = 0
        for block in self.blockChain:
            if block.miner == address:
                balance += block.reward

            for transaction in block.transactionStore.transactions:
                for (sender, amount) in transaction.senders:
                    if sender == address:
                        balance -= amount
                for (receiver, amount) in transaction.receivers:
                    if receiver == address:
                        balance += amount

        return balance

    def loadFromJSON(self, file: Union[str, bytes], overwrite=False) -> bool:
        lastSavedBlockHeight = self.currentHeight
        lastUpdated = "?"
        countUpdated = 0
        try:
            with open(file) as f:
                try:
                    data = json.load(f)
                    if overwrite:
                        self.blockChain = []
                        lastSavedBlockHeight = -1
                    elif (data['lastBlockHeight'] <= self.currentHeight):
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
                    if (data['lastBlockHeight'] > self.currentHeight):
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
            blockchain['lastBlockHeight'] = self.currentHeight

            f.truncate(0) # Erase file content
            f.write(json.dumps(blockchain))

        logging.info(f"Successfully saved {len(self.blockChain)} blocks to '{file}' [success]")
        return True