import unittest

from Blockchain import *


class MyTestCase(unittest.TestCase):
    def test_something(self):
        chain = Blockchain()
        chain.createGenesisBlock()
        print(str(chain.lastBlock))
        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()


