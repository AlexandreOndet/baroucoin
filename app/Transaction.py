from __future__ import annotations # Allows for using class type hinting within class (see https://stackoverflow.com/a/33533514)
from json import dumps

class Transaction:
    """Represents a transaction between two peers."""
    def __init__(self, senders: list, receivers: list):
        """Senders and receivers are a list of tuples with the addresses and the amounts."""
        total_in = 0
        for (addr, amount) in senders:
            total_in += amount
        # Ensure elements are tuples since they can be loaded from JSON (which dumps tuples as lists)
        self.senders = [tuple(t) for t in senders]

        total_out = 0
        for (addr, amount) in receivers:
            total_out += amount
        if total_out > total_in:
            raise ValueError("Sum of amount in must be >= Sum of amount out")
        # Ensure elements are tuples since they can be loaded from JSON (which dumps tuples as lists)
        self.receivers = [tuple(t) for t in receivers]

    def __repr__(self):
        return f"(in:{self.senders}, out:{self.receivers})"

    def toJSON(self):
        return dumps(self, default=lambda o: o.__dict__, sort_keys=True)

    @classmethod
    def fromJSON(cls, store: dict) -> Transaction:
        return cls(**store)