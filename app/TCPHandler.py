import socketserver
import json

'''
    See https://docs.python.org/3/library/socketserver.html#request-handler-objects for reference
'''
class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        fullnode = self.server
        request_sock = self.request # Peer connection

        data = request_sock.recv(1024)  # clip input at 1Kb
        text = data.decode('utf-8')
        json_payload = json.loads(text) # TODO : Handle exceptions
        print(f"Received from {self.client_address} : {json_payload}")

        request_sock.close()