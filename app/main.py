import sys
from threading import Thread

from FullNode import *
from dotenv import load_dotenv

load_dotenv()


'''
    usage : python main.py LOCALHOST_PORT WALLET_SALT [PEER_PORT ...]
'''
if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print(f"Usage : {sys.argv[0]} LOCALHOST_PORT WALLET_SALT [PEER_PORT ...]")
        exit(1)

    node = FullNode(consensusAlgorithm=False, existing_wallet=Wallet(sys.argv[0] + sys.argv[2]), server_address=("127.0.0.1", int(sys.argv[1])))
    json_save_file = node.wallet.address + ".json"

    node.blockchain.loadFromJSON(json_save_file, True)
    if (len(sys.argv) > 3):
        for port in sys.argv[3:]:
            if node.client.connect(("127.0.0.1", int(port))):
                print(f'[+] Connected to localhost:{port}')
    t = Thread(target=node.serve_forever).start()
    print(f"[*] FullNode (wallet: {node.wallet.address}) listening on localhost:{sys.argv[1]}...")
    
    run = True
    while run:
        user_input = ""
        while (user_input not in ['q', 'm', 'Q', 'M','s','S']):
            user_input = input("[x] Press m to start mining a new block, s to sync with other peers or q to quit :\n")
        if (user_input == 'q' or user_input == 'Q'):
            run = False
        else:
            if user_input == 's' or user_input == 'S':
                node.sync_with_peers()
                b = node.blockchain.lastBlock
                print(f"[+] Synced with peers, last block added is #{b.height} (hash: {b.getHash()}) !")
            else:
                node.mineNewBlock()
                b = node.blockchain.lastBlock
                print(f"[+] Mined block #{b.height} (hash: {b.getHash()}) !")

    node.client.broadcast({'end': node.server_address}) # Informs other peers to close the connection
    node.shutdown()
    node.blockchain.saveToJSON(json_save_file, True)