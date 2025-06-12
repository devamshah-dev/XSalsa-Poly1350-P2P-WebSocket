# main.py
import asyncio
import websockets
import json
import os
import shutil
from p2p_engine import P2PNetworkSimulator

# single global connection
NETWORK = P2PNetworkSimulator()
CONNECTED_CLIENTS = set()
SHUTDOWN_EVENT = asyncio.Event()
#API handler --> works now. 10/6/25

async def handle_create_peer(payload):
    name = payload.get("name")
    if not name:
        return {"success": False, "error": "Peer name is required."}
    NETWORK.create_peer(name)
    return {"success": True, "message": f"Peer '{name}' created."}

async def handle_connect_peers(payload):
    peer1 = payload.get("peer1")
    peer2 = payload.get("peer2")
    if not all([peer1, peer2]):
        return {"success": False, "error": "Both peer names are required."}
    success = NETWORK.connect_peers(peer1, peer2)
    if success:
        return {"success": True, "message": f"Connection between {peer1} and {peer2} established."}
    return {"success": False, "error": "Failed to connect peers."}

async def handle_send_message(payload):
    sender = payload.get("from")
    recipient = payload.get("to")
    message = payload.get("message")
    if not all([sender, recipient, message]):
        return {"success": False, "error": "Sender, recipient, and message are required."}
    # route the message --> works now 9/6/25
    await NETWORK.route_message(sender, recipient, message)
    # on_message_received callback sends a push & receiver gets the message via a server push.
    return {"success": True}

async def handle_get_history(payload):
    peer_a = payload.get("peer_a")
    peer_b = payload.get("peer_b")
    if not all([peer_a, peer_b]) or peer_a not in NETWORK.peers:
        return {"success": False, "error": "Invalid peers for history lookup."}
    
    history = NETWORK.peers[peer_a].get_conversation_history(peer_b)
    return {"success": True, "history": history}

# handler for shutdown command
async def handle_shutdown(payload):
    print("[SERVER] Shutdown command received. Shutting down in 3 seconds...")
    await asyncio.sleep(1) 
    SHUTDOWN_EVENT.set() # Trigger global shutdown event
    return {"success": True, "message": "Server is shutting down."}

#WebSocket Server Logic --> finally runs: 9/6/25
async def broadcast(message):
    #sends a message to all clients.
    if CONNECTED_CLIENTS:
        await asyncio.wait([client.send(message) for client in CONNECTED_CLIENTS])

async def event_handler(event):
    """Callback for events from the P2P engine."""
    print(f"P2P Engine Event: {event}")
    await broadcast(json.dumps(event))

async def handler(websocket, path):
    #main WebSocket connection handler
    CONNECTED_CLIENTS.add(websocket)
    print(f"Client connected. Total clients: {len(CONNECTED_CLIENTS)}")
    
    #network event handler to async broadcast function --> final implementation: 7/6/25
    NETWORK.set_event_handler(event_handler)

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get("action")
                payload = data.get("payload", {})
                
                response = {"success": False, "error": "Unknown action"}

                if action == "create_peer":
                    response = await handle_create_peer(payload)
                elif action == "connect_peers":
                    response = await handle_connect_peers(payload)
                elif action == "send_message":
                    response = await handle_send_message(payload)
                elif action == "get_history":
                    response = await handle_get_history(payload)
                elif action == "shutdown":
                    response = await handle_shutdown(payload)
                # send response backto client (requests)
                await websocket.send(json.dumps({"type": "response", "action": action, "data": response}))

            except json.JSONDecodeError:
                await websocket.send(json.dumps({"success": False, "error": "Invalid JSON"}))
            except Exception as e:
                await websocket.send(json.dumps({"success": False, "error": str(e)}))
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        print(f"Client disconnected. Total clients: {len(CONNECTED_CLIENTS)}")

async def main():
    # reset old data
    if os.path.exists("keys"): shutil.rmtree("keys")
    if os.path.exists("encrypted"): shutil.rmtree("encrypted")
    os.makedirs("keys", exist_ok=True)
    os.makedirs("encrypted", exist_ok=True)
    port = 8765
    server = await websockets.serve(handler, "localhost", port)
    print(f"WebSocket server started on ws://localhost:{port}")
    await SHUTDOWN_EVENT.wait()
    server.close()
    await server.wait_closed()
    print("WebSocket server has shut down.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
         print("\nServer stopped by peer.")
    