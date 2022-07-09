from Transaction import *

class TransactionStore(dict):
    def __init__(self, transactions: Transaction = None):
        super(TransactionStore, self).__init__()
        self.transactions = transactions if transactions != None else []
    
    def __str__(self):
        return str(self.transactions)

    def __repr__(self):
        return str(self.transactions)

    def addTransaction(self, transaction: Transaction):
        self.transactions.append(transaction)
