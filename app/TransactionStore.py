import Transaction


class TransactionStore(dict):
    def __init__(self, transactions: Transaction = []):
        super(TransactionStore, self).__init__()
        self.transactions = transactions

    def addTransaction(self, transaction: Transaction):
        self.transactions.append(transaction)
