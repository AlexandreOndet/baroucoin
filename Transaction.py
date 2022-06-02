class Transaction:
    def __init__(self, senders, receivers):
        tmp = 0
        for i in senders:
            tmp += i[1]
        if tmp != 1.0:
            raise ValueError("Sum of coefs for senders it not equal to one")
        self.senders = []  # tuples with address (string) and coef double. Sum of coefs must be equal to 1.0

        tmp = 0
        for i in receivers:
            tmp += i[1]
        if tmp != 1.0:
            raise ValueError("Sum of coefs for receivers it not equal to one")
        self.receivers = []
