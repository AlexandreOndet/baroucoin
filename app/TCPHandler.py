import logging
import socketserver
from typing import Callable

from app.Block import *
from app.TransactionStore import *

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
            try:
                data = self.request.recv(4096)  # TODO : Fix in case payload gets bigger than 4Kb

                text = data.decode("utf-8")

                json_payload = json.loads(text)  # TODO : Handle exceptions
                self._log(logging.debug,
                          f"Received {len(data)} bytes from {self.client_address} :\n{json.dumps(json_payload, indent=4, sort_keys=True)}\n")
                keep_alive = self.parseJSON(json_payload)
            except Exception as e:
                self._log(logging.error, f"Exception in TCPHandler {e}")
                keep_alive = False

        self.request.close()
        self._log(logging.info, f"Closed connection with {self.client_address} [success]")

    def getLastBlock(self, data, sender_address):
        peer_adress = sender_address  # self.client_address
        self._log(logging.debug, f"Received getLastBlock request from {peer_adress} with data : {data}")
        data = json.loads(data)
        receivedLastBlockHash = data["latestBlockHash"]
        if receivedLastBlockHash != self.fullnode.blockchain.lastBlock.getHash():
            self.fullnode.send_last_block(peer_adress)
        return True

    def receiveMyLastBlock(self, data, sender_address):
        self._log(logging.debug, f"[+] Received 'receiveMyLastBlock' request, checking if different from current block")
        data = json.loads(data)
        receivedLastBlockHash = data["latestBlockHash"]
        if receivedLastBlockHash != self.fullnode.blockchain.lastBlock.getHash():
            peer_adress = sender_address  # self.client_address
            receivedLastBlockHeight = data["lastBlockHeight"]
            self._log(logging.info, f"[+] Asking for inventory")
            self.fullnode.ask_inventory(peer_adress, receivedLastBlockHash, receivedLastBlockHeight)
        return True

    def askingForInventory(self, data, sender_address):
        peer_address = sender_address  # self.client_address
        data = json.loads(data)
        from_height = data["from"]
        to_height = data["to"]
        self._log(logging.info, f"[+] Asked to send inventory from {from_height} to {to_height} height")
        self.fullnode.returnInventory(peer_address, from_height, to_height)
        return True

    def returnInventory(self, data, sender_address):
        data = json.loads(data)
        self._log(logging.info, f"[+] Received inventory")
        received_block_height = data["block_height"]
        block_json_obj = json.loads(data["block_json"])
        block = Block.fromJSON(block_json_obj)
        if (self.fullnode.validateNewBlock(block) and block.height == received_block_height):
            self._log(logging.info,
                      f"[+] Validated new block from inventory #{block.height} (hash: {block.getHash()}) !")
            self.fullnode.blockchain.blockchain[received_block_height] = block
        return True

    def parseJSON(self, data: dict) -> bool:
        for method in list(data.keys()):
            if (method in self.whitelistedFunctions):
                # TODO : See if general deserialization approach is feasible and handle exception on method not found
                return getattr(self, method)(data[method], data["sender_address"])

    def connect(self, data, sender_address) -> bool:
        server_address = tuple(data)  # TODO : Add deserialization checks
        if (self.fullnode.client.connect(server_address)):
            self._log(logging.info, f"Connected back to {server_address} [success]")
        else:
            self._log(logging.warning, f"Already connected to {server_address}")
        return True

    def newBlock(self, data, sender_address) -> bool:
        data = json.loads(data)  # TODO : Add deserialization checks
        data['transactionStore'] = TransactionStore.fromJSON(data['transactionStore']);
        block = Block.fromJSON(data)
        if (self.fullnode.validateNewBlock(block)):
            self._log(logging.info, f"Validated block #{block.height} (hash: {block.getHash()}) [success]")
            self.fullnode.blockchain.addBlock(block)
        else:
            self._log(logging.warning,
                      f"Block #{block.height} invalid: hash={block.getHash()}, lastBlock.height={self.fullnode.blockchain.lastBlock.height}")
        return True

    def end(self, data, sender_address) -> bool:
        server_address = tuple(data)  # TODO : Add deserialization checks
        self._log(logging.info, f"Received disconnect request from {server_address}")
        self.fullnode.client.disconnect(server_address)  # Disconnects but do not remove the peer from the peers list
        return False

    def _log(self, level_func: Callable, msg: str):
        level_func(f"[{self.fullnode.id}] " + msg)
