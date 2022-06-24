class Transaction:
    def __init__(self, senders, receivers):
        total_in = 0
        for i in senders:
            total_in += i[1]
        self.senders = []  # tuples with address (string) and amount of coins.

        total_out = 0
        for i in receivers:
            total_out += i[1]
        if total_out > total_in:
            raise ValueError("Sum of amount in must be >= Sum of amount out")
        self.receivers = []

    def __repr__(self):
        return f"in:{self.senders}, out:{self.receivers}"