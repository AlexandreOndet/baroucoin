import hashlib as h
from json import dumps

class Block:
    def __init__(self, id, time, transactions, status, difficulty, last_hash, nonce):
        self.id=id
        self.time=time
        self.transactions=transactions
        self.status=status #number of confimations (is it in the longest branch)
        self.difficulty=difficulty #for the PoW
        self.last_hash=last_hash
        self.nonce=nonce

    def getHash(self):
        block= dumps(self.__dict__, sort_keys=True)
        return h.sha3_256(block.encode()).hexdigest()