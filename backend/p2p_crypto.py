import os
import base64
import json
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
import nacl.secret
import nacl.public
import nacl.utils
from nacl.public import PrivateKey, PublicKey, Box
from nacl.secret import SecretBox
from nacl.encoding import Base64Encoder
from nacl.hash import blake2b
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from datetime import datetime, timezone

class CryptoManager:
    """
    - XChaCha20-Poly1305 encryption/decryption
    - ECDH key exchange
    - Key generation and storage
    """
    
    def __init__(self, keys_dir: str = "keys"):
        self.keys_dir = keys_dir
        self.ensure_keys_directory()
        
    def ensure_keys_directory(self):
        """creating keys directory"""
        if not os.path.exists(self.keys_dir):
            os.makedirs(self.keys_dir)
    
    def generate_keypair(self, peer_name: str) -> Tuple[str, str]:
        """private_key base64, public_key base64"""
        private_key = PrivateKey.generate()
        public_key = private_key.public_key
        
        # ennncoding keys in Base64
        private_key_b64 = base64.b64encode(private_key.encode()).decode('utf-8')
        public_key_b64 = base64.b64encode(public_key.encode()).decode('utf-8')
        
        # saving private key to file
        self.save_private_key(peer_name, private_key_b64)
        
        return private_key_b64, public_key_b64
    
    def save_private_key(self, peer_name: str, private_key_b64: str):
        """saving private key to keys/ directory"""
        key_file = os.path.join(self.keys_dir, f"{peer_name}_private.key")
        key_data = {
            "peer_name": peer_name,
            "private_key": private_key_b64,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "key_type": "ECDH_X25519"
        }
        with open(key_file, 'w') as f:
            json.dump(key_data, f, indent=2)
        print(f"Private key saved for {peer_name}: {key_file}")
    
    def load_private_key(self, peer_name: str) -> Optional[str]:
        """load private key from keys dir"""
        key_file = os.path.join(self.keys_dir, f"{peer_name}_private.key")
        if not os.path.exists(key_file):
            return None 
        try:
            with open(key_file, 'r') as f:
                key_data = json.load(f)
            return key_data["private_key"]
        except Exception as e:
            print(f"Error loading private key --> {peer_name}: {e}")
            return None
    
    def derive_shared_secret(self, my_private_key_b64: str, peer_public_key_b64: str) -> bytes:
        """shared secret using ECDH"""
        try:
            # decoding Base64 keys
            my_private_key = PrivateKey(base64.b64decode(my_private_key_b64))
            peer_public_key = PublicKey(base64.b64decode(peer_public_key_b64))
            # boxing for ECDH
            box = Box(my_private_key, peer_public_key)
            # 32 bytes for XChaCha20S
            return box.shared_key()
            
        except Exception as e:
            raise Exception(f"Failed to derive shared secret keys: {e}")
    
    def encrypt_message(self, message: str, shared_secret: bytes) -> Dict[str, Any]:
        """encryptinng message using XChaCha20-Poly1305"""
        try:
            # random nonce (24 bytes for XChaCha20)
            nonce = nacl.utils.random(24)
            # secretBoxy with shared secret
            box = nacl.secret.SecretBox(shared_secret)
            # eencrypt message
            message_bytes = message.encode('utf-8')
            encrypted = box.encrypt(message_bytes, nonce)
            # extract ciphertext
            ciphertext = encrypted.ciphertext
            return {
                "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
                "nonce": base64.b64encode(nonce).decode('utf-8'),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "algorithm": "XChaCha20-Poly1305"
            }
        except Exception as e:
            raise Exception(f"Encryption failed: {e}")
    
    def decrypt_message(self, encrypted_data: Dict[str, Any], shared_secret: bytes) -> str:
        """decrypting de message using XChaCha20-Poly1305"""
        try:
            # decode Base64 data
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
            nonce = base64.b64decode(encrypted_data["nonce"])
            # create SecretBox with shared secret
            box = nacl.secret.SecretBox(shared_secret)
            # decrypt message
            decrypted = box.decrypt(ciphertext, nonce)
            return decrypted.decode('utf-8')
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")
    
    def hash_data(self, data: str) -> str:
        """creating Blake2b hash of data"""
        hash_bytes = blake2b(data.encode('utf-8'), digest_size=32)
        return base64.b64encode(hash_bytes).decode('utf-8')
    
    def verify_message_integrity(self, message: str, hash_b64: str) -> bool:
        """verifing message integrity using hash"""
        try:
            calculated_hash = self.hash_data(message)
            return calculated_hash == hash_b64
        except:
            return False
class P2PSession:
    """manages a P2P session between two peers"""
    def __init__(self, my_name: str, peer_name: str, crypto_manager: CryptoManager):
        self.my_name = my_name
        self.peer_name = peer_name
        self.crypto_manager = crypto_manager
        self.shared_secret = None
        self.my_private_key = None
        self.my_public_key = None
        # load my keypair
        self.initialize_keys()
    
    def initialize_keys(self):
        """initialize or load keypair for this peer"""
        self.my_private_key = self.crypto_manager.load_private_key(self.my_name)
        if not self.my_private_key:
            # generating new keypair
            self.my_private_key, self.my_public_key = self.crypto_manager.generate_keypair(self.my_name)
        else:
            # deriving public key from private key
            private_key_obj = PrivateKey(base64.b64decode(self.my_private_key))
            self.my_public_key = base64.b64encode(private_key_obj.public_key.encode()).decode('utf-8')
    
    def establish_session(self, peer_public_key_b64: str):
        """establishing session with peer using their public key"""
        try:
            assert self.my_private_key is not None, "Private key must be initialized"
            self.shared_secret = self.crypto_manager.derive_shared_secret(
                self.my_private_key, 
                peer_public_key_b64
            )
            print(f"Session established between {self.my_name} and {self.peer_name}")
            return True
        except Exception as e:
            print(f"Failed to establish session: {e}")
            return False
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """enccrypting and prepare message for sending"""
        if not self.shared_secret:
            raise Exception("Session not established")
        encrypted_data = self.crypto_manager.encrypt_message(message, self.shared_secret)
        
        # adding metadata
        message_packet = {
            "from": self.my_name,
            "to": self.peer_name,
            "message_id": self.crypto_manager.hash_data(f"{message}{encrypted_data['timestamp']}"),
            "encrypted_data": encrypted_data,
            "session_established": True
        }
        return message_packet
    
    def receive_message(self, message_packet: Dict[str, Any]) -> str:
        """decrypting received message"""
        if not self.shared_secret:
            raise Exception("Session not established")
        if message_packet["to"] != self.my_name:
            raise Exception("Message not intended for this peer")
        decrypted_message = self.crypto_manager.decrypt_message(
            message_packet["encrypted_data"], 
            self.shared_secret
        )
        return decrypted_message
    
    def get_my_public_key(self) -> str:
        assert self.my_public_key is not None, "public key must be initialized"
        """return my public key for sharing"""
        return self.my_public_key


# utility functions for easy usage
def create_peer_session(my_name: str, peer_name: str, keys_dir: str = "keys") -> P2PSession:
    """creating a new P2P session"""
    crypto_manager = CryptoManager(keys_dir)
    return P2PSession(my_name, peer_name, crypto_manager)

def generate_qr_data(peer_name: str, public_key: str, ip_address: str = "192.168.1.100", port: int = 5000) -> Dict[str, Any]:
    """generating data for QR code to bootstrap P2P connection"""
    return {
        "peer_name": peer_name,
        "public_key": public_key,
        "ip_address": ip_address,
        "port": port,
        "protocol": "p2p-messaging-v1",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    # tesing the crypto system
    print("Testing Peer2Peer messaging System...")
    # creation sessions for Alice and Bob
    alice_session = create_peer_session("Alice", "Bob")
    bob_session = create_peer_session("Bob", "Alice")
    # exchange public keys and establish sessions
    alice_pubkey = alice_session.get_my_public_key()
    bob_pubkey = bob_session.get_my_public_key()
    alice_session.establish_session(bob_pubkey)
    bob_session.establish_session(alice_pubkey)
    
    # testin message exchange
    message = "Hello Bob! This is a secure P2P message."
    encrypted_packet = alice_session.send_message(message)
    decrypted_message = bob_session.receive_message(encrypted_packet)
    
    print(f"Original: {message}")
    print(f"Decrypted: {decrypted_message}")
    print(f"Success: {message == decrypted_message}")