import Transaction


class TransactionStore:
    def __init__(self, transactions: Transaction = []):
        self.transactions = transactions

    def addTransaction(self, transaction: Transaction):
        self.transactions.append(transaction)
