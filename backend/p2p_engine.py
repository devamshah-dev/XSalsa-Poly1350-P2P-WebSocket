# p2p_engine.py

import json
import time
from typing import Dict, Any, List, Callable, Optional, Coroutine
from p2p_crypto import create_peer_session
from file_store import create_message_store
from datetime import datetime
import asyncio

class P2PPeer:
    def __init__(self, name: str, ip_address: str = "127.0.0.1", port: int = 5000):
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.sessions: Dict[str, Any] = {}
        self.message_store = create_message_store() 
        self.on_message_received: Optional[Callable[[Dict], Coroutine[Any, Any, None]]] = None

    def connect_to_peer(self, peer_name: str, peer_public_key: str) -> bool:
        try:
            if peer_name not in self.sessions:
                self.sessions[peer_name] = create_peer_session(self.name, peer_name)
            return self.sessions[peer_name].establish_session(peer_public_key)
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def send_message(self, peer_name: str, message: str) -> Optional[Dict[str, Any]]:
        if peer_name not in self.sessions:
            return None
        try:
            message_packet = self.sessions[peer_name].send_message(message)
            self.message_store.save_message(message_packet, peer_name)
            return message_packet
        except Exception as e:
            print(f"Send message error: {e}")
            return None

    async def receive_message(self, message_packet: Dict[str, Any]):
        sender = message_packet.get("from")
        if not isinstance(sender, str) or sender not in self.sessions:
            return
        try:
            decrypted_message = self.sessions[sender].receive_message(message_packet)
            self.message_store.save_message(message_packet, sender)
            # creates simple display message format
            display_msg = {
                "from": sender,
                "to": self.name,
                "message": decrypted_message,
                "timestamp": datetime.now().isoformat()
            }
            # use the callback to notify the higher level (WebSocket server)
            if self.on_message_received:
                asyncio.create_task(self.on_message_received(display_msg))
        except Exception as e:
            print(f"Receive message error: {e}")

    def get_my_public_key(self, peer_name: str) -> Optional[str]:
        if peer_name not in self.sessions:
            temp_session = create_peer_session(self.name, peer_name)
            return temp_session.get_my_public_key()
        return self.sessions[peer_name].get_my_public_key()

    def get_conversation_history(self, peer_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        if peer_name not in self.sessions:
            return []
        stored_messages = self.message_store.get_messages_by_peer(peer_name)
        conversation = []
        session = self.sessions[peer_name]
        for msg_data in stored_messages[-limit:]:
            try:
                packet = msg_data["message_packet"]
                decrypted = session.receive_message(packet)
                conversation.append({
                    "from": packet["from"],
                    "to": packet["to"],
                    "message": decrypted,
                    "timestamp": msg_data["stored_at"],
                })
            except Exception:
                continue
        return conversation

class P2PNetworkSimulator:
    def __init__(self):
        self.peers: Dict[str, P2PPeer] = {}
        self.on_event: Optional[Callable[[Dict], Coroutine[Any, Any, None]]] = None

    def set_event_handler(self, handler: Callable[[Dict], Coroutine[Any, Any, None]]):
        #sets callback for network-wide events.
        self.on_event = handler

    def create_peer(self, name: str) -> P2PPeer:
        if name in self.peers:
            return self.peers[name]
        peer = P2PPeer(name)
        # hook message receiver to network-wide event handler --> solved error:17
        peer.on_message_received = self._handle_peer_event
        self.peers[name] = peer
        return peer

    def connect_peers(self, peer1_name: str, peer2_name: str) -> bool:
        if peer1_name not in self.peers or peer2_name not in self.peers:
            return False
        peer1 = self.peers[peer1_name]
        peer2 = self.peers[peer2_name]
        key1 = peer1.get_my_public_key(peer2_name)
        key2 = peer2.get_my_public_key(peer1_name)
        if not key1 or not key2: return False
        res1 = peer1.connect_to_peer(peer2_name, key2)
        res2 = peer2.connect_to_peer(peer1_name, key1)
        return res1 and res2

    async def route_message(self, from_peer: str, to_peer: str, message: str):
        if from_peer in self.peers and to_peer in self.peers:
            sender = self.peers[from_peer]
            receiver = self.peers[to_peer]
            message_packet = sender.send_message(to_peer, message)
            if message_packet:
                import asyncio
                await receiver.receive_message(message_packet)

    async def _handle_peer_event(self, event_data: Dict):
        #internal handler to propagate events up to the WebSocket server.
        if self.on_event:
            asyncio.create_task(self.on_event({
                "type": "new_message",
                "data": event_data
            }))