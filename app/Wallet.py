import base58
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import *


class Wallet(object):
    """Wallet associated with a full node."""

    def __init__(self, seed: str, display_name=""):
        super(Wallet, self).__init__()
        self.display_name = display_name
        self.balance = 0
        self.secret_key = self.generate_keys(seed.encode('utf-8'))
        self.address = self.generate_address()

    def generate_keys(self, seed: bytes) -> ec.EllipticCurvePrivateKey:
        salt = b'' # Empty salt for the purpose of generating the same addresses (useful for the simulation)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200_000)
        dk = kdf.derive(seed)
        return ec.derive_private_key(int.from_bytes(dk, "big"),
                                     ec.SECP256K1())  # An EllipticCurvePrivateKey object (see https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ec/#cryptography.hazmat.primitives.asymmetric.ec.EllipticCurvePrivateKey)

    def generate_address(self) -> bytes:  # Address is a base58 encoded hash derived from the public key
        digest = hashes.Hash(hashes.SHA256())
        digest.update(self.secret_key.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo))
        return base58.b58encode(digest.finalize()).decode('utf-8') # Store address as string

    def addToBalance(self, amount: int):
        if amount <= 0:
            raise ValueError("Amount cannot be negative or zero")
        self.balance += amount

    def removeFromBalance(self, amount: int):
        if amount <= 0:
            raise ValueError("Amount cannot be negative or zero")
        if self.balance - amount < 0:
            raise ValueError("Balance cannot be negative")
        self.balance -= amount

    def show_private_key(self):
        print(self.secret_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode('utf-8'))

    def show_public_key(self):
        print(
            self.secret_key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode('utf-8'))

    def show_info(self):
        if self.display_name:
            print(f"=== {self.display_name} ===")
        print(f"Address : {self.address.decode()}")
        print(f"Balance : {self.balance} baroucoin")