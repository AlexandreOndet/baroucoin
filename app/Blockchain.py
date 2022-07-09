import time
import json
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

        genesisBlock.hash = genesisBlock.getHash()
        self.blockChain.append(genesisBlock)

    @property
    def lastBlock(self):
        return self.blockChain[-1]

    def addBlock(self, block: Block):
        self.blockChain.append(block)

    def loadFromJSON(self, file: Union[str, bytes]):
        pass
        # with open(file) as f:
        # 	data = json.load(f)
        # 	for block in data:
        # 		self.transaction_pool.append(Transaction(list(t['senders']), list(t['receivers'])))
        # 	f.close()

    def saveToJSON(self, file: Union[str, bytes], overwrite=False):
        blockchain = {} # JSON object to save blockchain data
        lastSavedBlockHeight = 0
        with open(file, 'a+') as f: # 'a+' enables reading AND writing to file AND create it if it does not yet exists
            blockchain['blocks'] = []

            if not overwrite:
                f.seek(0) # Go back to start of file since it's opened in 'append' mode
                try:
                    data = json.loads(f.read())
                    if (data['lastBlockHeight'] > self.lastBlock.height):
                        print("[-] Saving aborted: previously saved blockchain is longer than current blockchain (set overwrite=True to force save)")
                        return

                    # Add previously saved blocks to the new save file
                    lastSavedBlockHeight = data['lastBlockHeight']
                    previousBlocks = data['blocks']
                    for block in previousBlocks:
                        blockchain['blocks'].append(block.toJSON())
                except Exception as e:
                    print(f"[!] File not found, creating new file...")

            for block in self.blockChain:
                if (block.height >= lastSavedBlockHeight):
                    blockchain['blocks'].append(block.toJSON())

            blockchain['savedTime'] = time.time()
            blockchain['lastBlockHeight'] = self.lastBlock.height

            f.truncate(0) # Erase file content
            f.write(json.dumps(blockchain))

        print(f"[+] Successfully saved {len(self.blockChain)} blocks to {file} !")