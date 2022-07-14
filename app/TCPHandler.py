import socketserver
import json

from Block import *
from TransactionStore import *

'''
    See https://docs.python.org/3/library/socketserver.html#request-handler-objects for reference
'''


class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.whitelistedFunctions = ['connect', 'newBlock', 'end', 'getLastBlock',
                                     'receiveMyLastBlock', 'askingForInventory',
                                     'returnInventory']  # TODO : Load from env ?
        self.fullnode = self.server
        keep_alive = True

        while (keep_alive):
            data = self.request.recv(4096)  # TODO : Fix in case payload gets bigger than 4Kb

            text = data.decode("utf-8")
            try:
                json_payload = json.loads(text)  # TODO : Handle exceptions
                print(
                    f"[DEBUG] Received {len(data)} bytes from {self.client_address} :\n{json.dumps(json_payload, indent=4, sort_keys=True)}\n")
                keep_alive = self.parseJSON(json_payload)
            except Exception as e:
                keep_alive = False

        self.request.close()
        print(f"[+] Closed connection with {self.client_address}")

    def getLastBlock(self, data):
        peer_adress = self.client_address
        receivedLastBlockHash = data["getLastBlock"]
        if receivedLastBlockHash != self.fullnode.blockchain.lastBlock.getHash():
            self.fullnode.send_last_block(peer_adress)

    def receiveMyLastBlock(self, data):
        receivedLastBlockHash = data["receiveMyLastBlock"]
        if receivedLastBlockHash != self.fullnode.blockchain.lastBlock.getHash():
            peer_adress = self.client_address
            receivedLastBlockHeight = data["lastBlockHeight"]
            self.fullnode.ask_inventory(peer_adress, receivedLastBlockHash, receivedLastBlockHeight)

    def askingForInventory(self, data):
        peer_address = self.client_address
        from_height = data["from"]
        to_height = data["to"]
        self.fullnode.returnInventory(peer_address, from_height, to_height)

    def returnInventory(self, data):
        received_block_height = data["block_height"]
        block = Block.fromJSON(data)
        if (self.fullnode.validateNewBlock(block) and block.height == received_block_height):
            print(f"[+] Received and validated new block from inventory #{block.height} (hash: {block.getHash()}) !")
            self.fullnode.blockchain.blockchain[received_block_height] = block

    def parseJSON(self, data: dict) -> bool:
        for method in list(data.keys()):
            if (method in self.whitelistedFunctions):
                # TODO : See if general deserialization approach is feasible and handle exception on method not found
                return getattr(self, method)(data[method])

    def connect(self, data) -> bool:
        server_address = tuple(data)  # TODO : Add deserialization checks
        if (self.fullnode.client.connect(server_address)):
            print(f"[*] Connected back to {server_address}...")
        else:
            print(f"[!] Already connected to {server_address} !")

        return True

    def newBlock(self, data) -> bool:
        data = json.loads(data);  # TODO : Add deserialization checks
        data['transactionStore'] = TransactionStore.fromJSON(data['transactionStore']);
        block = Block.fromJSON(data)
        if (self.fullnode.validateNewBlock(block)):
            print(f"[+] Validated block #{block.height} (hash: {block.getHash()}) !")
            self.fullnode.blockchain.addBlock(block)
        else:
            print(
                f"[!] Block #{block.height} invalid: hash={block.getHash()}, lastBlock.height={self.fullnode.blockchain.lastBlock.height}")
        return True

    def end(self, data) -> bool:
        server_address = tuple(data)  # TODO : Add deserialization checks
        self.fullnode.client.disconnect(server_address)  # Disconnects but do not remove the peer from the peers list
        return False
