from __future__ import annotations # Allows for using class type hinting within class (see https://stackoverflow.com/a/33533514)
from app.Transaction import *

import json

class TransactionStore(dict):
    """Stores all transactions within a block."""
    def __init__(self, transactions: list(Transaction) = None):
        super(TransactionStore, self).__init__()
        self.transactions = transactions if transactions != None else []
    
    def __str__(self):
        return str(self.transactions)

    def __repr__(self):
        return str(self.transactions)

    @property
    def isEmpty(self):
        return len(self.transactions) > 0

    def addTransaction(self, transaction: Transaction):
        self.transactions.append(transaction)
    
    @classmethod
    def fromJSON(cls, store: list) -> TransactionStore:
        return cls(transactions=[Transaction.fromJSON(json.loads(t)) for t in store])