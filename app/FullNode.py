from Blockchain import *
from Wallet import *
from Transaction import *

class FullNode(object):
	"""docstring for FullNode"""
	def __init__(self, existing_wallet=Wallet()):
		super(FullNode, self).__init__()
		self.wallet = existing_wallet
		self.transaction_pool = []
		self.blockchain = Blockchain() # Should the FullNode class search for existing blockchain or should the constructor of Blockchain do it ?

	def addToTransactionPool(self, t: Transaction):
		self.transaction_pool.append(t)