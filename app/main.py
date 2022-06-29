import sys
import random
from threading import Thread

from FullNode import *
from dotenv import load_dotenv

load_dotenv()


'''
    usage : python main.py LOCALHOST_PORT [PEER_PORT ...]
'''
if __name__ == "__main__":
    node = FullNode(consensusAlgorithm=False, existing_wallet=Wallet(sys.argv[0] + str(random.randint(1, 1000))), server_address=("localhost", int(sys.argv[1])))
    node.blockchain.createGenesisBlock()
    if (len(sys.argv) > 2):
        for port in sys.argv[2:]:
            if node.client.connect(("localhost", int(port))):
                print(f'[+] Connected to localhost:{port}')
    t = Thread(target=node.serve_forever).start()
    print(f"[*] FullNode (wallet: {node.wallet.address}) listening on localhost:{sys.argv[1]}...")
    
    run = True
    while run:
        user_input = ""
        while (user_input not in ['q', 'm', 'Q', 'M']):
            user_input = input("[x] Press m to start mining a new block or q to quit :\n")

        if (user_input == 'q' or user_input == 'Q'):
            run = False
        else:
            node.mineNewBlock()
            b = node.blockchain.lastBlock
            print(f"[+] Mined block #{b.height} (hash: {b.getHash()}) !")

    node.client.broadcast({'end': True}) # Informs other peers to close the connection
    node.shutdown()