from fastapi import FastAPI, Request

blockchain = FastAPI()

chain = [] # Replace by our blockchain object later on


@blockchain.get("/test")
def test_hello_word():
    return {"Barou": "COIN ! "}


@blockchain.get("/")
async def index():
    """
    Index endpoint for Blockchain server.
    :return: str
    """
    return "Index"


@blockchain.get("/mainchain")
async def b_chain() -> dict:
    """
    Ledger endpoint for Blockchain server. Returns the current state of the blockchain.
    :return: dict -> keys: chain:Lis[dict] -> Serialized Blocks
    """
    return {"current_chain": chain.blocks}


@blockchain.get("/peers")
async def peers() -> dict:
    """
    Peers List endpoint for Blockchain Server.
    :return: dict -> keys: peers: List[str]
    """
    ips = [peer.ip for peer in chain.peers]
    return {"peers": ips}


@blockchain.post("/new-peer")
async def new_peer(request: Request) -> dict:
    """
    Adds a new peer to the blockchain network
    :param request: Request -> HTTP POST request.
    :return: dict -> keys: new_peer:str -> IP Address
    """
    peer_host = request.client.host
    peer_port = request.client.port
    if peer_host == "127.0.0.1":
        address = f"{chain.server_address}"
    else:
        address = f"http://{peer_host}:{peer_port}"
    print(address)
    chain.peers.add(address)
    return {"new_peer added ": address}
