import os
import json
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
import msgpack
from datetime import datetime, timezone

class MessageStore:
    """handles storage and retrieval of encrypted messages and files"""
    
    def __init__(self, encrypted_dir: str = "encrypted"):
        self.encrypted_dir = encrypted_dir
        self.ensure_directories()
    def ensure_directories(self):
        """create necessary directories"""
        dirs = [
            self.encrypted_dir,
            os.path.join(self.encrypted_dir, "messages"),
            os.path.join(self.encrypted_dir, "files"),
            os.path.join(self.encrypted_dir, "metadata")
        ]
        for dir_path in dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
    def save_message(self, message_packet: Dict[str, Any], peer_name: str) -> str:
        """saving encrypted message to file & returns ass message_id"""
        message_id = message_packet.get("message_id")
        if not message_id:
            message_id = self._generate_message_id(message_packet)
        
        # createion of message file path
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{peer_name}_{timestamp}_{message_id[:8]}.msg"
        file_path = os.path.join(self.encrypted_dir, "messages", filename)
        
        # Add storage metadata
        storage_data = {
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "file_path": file_path,
            "message_packet": message_packet,
            "peer_name": peer_name,
            "message_type": "text"
        }
        # save to file
        with open(file_path, 'w') as f:
            json.dump(storage_data, f, indent=2)
        # update metadata index
        self.update_message_index(message_id, file_path, peer_name, "text")
        print(f"Message saved: {file_path}")
        return message_id
    
    def save_file_message(self, file_data: bytes, filename: str, message_packet: Dict[str, Any], peer_name: str) -> str:
        """save encrypted file message & returns as message_id"""
        message_id = message_packet.get("message_id")
        if not message_id:
            message_id = self._generate_message_id(message_packet)
        # create file paths
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_filename = self._safe_filename(filename)
        # save encrypted file data
        file_path = os.path.join(self.encrypted_dir, "files", f"{peer_name}_{timestamp}_{safe_filename}")
        with open(file_path, 'wb') as f:
            f.write(file_data)
        # save message metadata
        metadata_file = os.path.join(self.encrypted_dir, "metadata", f"{message_id}.json")
        metadata = {
            "message_id": message_id,
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "file_path": file_path,
            "original_filename": filename,
            "file_size": len(file_data),
            "message_packet": message_packet,
            "peer_name": peer_name,
            "message_type": "file"
        }
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        # update message index
        self.update_message_index(message_id, file_path, peer_name, "file", filename)
        print(f"File message saved: {file_path}")
        return message_id
    
    def load_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        #load message by ID
        index = self._load_message_index()
        if message_id not in index:
            return None
        entry = index[message_id]
        if entry["message_type"] == "text":
            # load text message
            try:
                with open(entry["file_path"], 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                return None
        elif entry["message_type"] == "file":
            # load file message metadata
            metadata_file = os.path.join(self.encrypted_dir, "metadata", f"{message_id}.json")
            try:
                with open(metadata_file, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                return None
        return None
    
    def load_file_data(self, message_id: str) -> Optional[bytes]:
        """load encrypted file data by message ID"""
        message_data = self.load_message(message_id)
        if not message_data or message_data.get("message_type") != "file":
            return None
        try:
            with open(message_data["file_path"], 'rb') as f:
                return f.read()
        except FileNotFoundError:
            return None
    def get_messages_by_peer(self, peer_name: str) -> List[Dict[str, Any]]:
        """gettting all messages from/to a specific peer"""
        index = self._load_message_index()
        peer_messages = []
        for message_id, entry in index.items():
            if entry["peer_name"] == peer_name:
                message_data = self.load_message(message_id)
                if message_data:
                    peer_messages.append(message_data)
        # sort by timestamp
        peer_messages.sort(key=lambda x: x.get("stored_at", ""))
        return peer_messages
    
    def get_recent_messages(self, limit: int = 50) -> List[Dict[str, Any]]:
        """get recent messages (all peers)"""
        index = self._load_message_index()
        all_messages = []
        for message_id in index:
            message_data = self.load_message(message_id)
            if message_data:
                all_messages.append(message_data)
        # sort by timestamp (newest first)
        all_messages.sort(key=lambda x: x.get("stored_at", ""), reverse=True)
        return all_messages[:limit]
    
    def delete_message(self, message_id: str) -> bool:
        """delete a message and its files"""
        index = self._load_message_index()
        if message_id not in index:
            return False
        entry = index[message_id]
        try:
            # delete main file
            if os.path.exists(entry["file_path"]):
                os.remove(entry["file_path"])
            # delete metadata file for file messages
            if entry["message_type"] == "file":
                metadata_file = os.path.join(self.encrypted_dir, "metadata", f"{message_id}.json")
                if os.path.exists(metadata_file):
                    os.remove(metadata_file)
            # remove from index
            del index[message_id]
            self._save_message_index(index)
            print(f"Message {message_id} deleted")
            return True
        except Exception as e:
            print(f"Error deleting message {message_id}: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        #get storage statistics
        index = self._load_message_index() 
        total_messages = len(index)
        text_messages = sum(1 for entry in index.values() if entry["message_type"] == "text")
        file_messages = sum(1 for entry in index.values() if entry["message_type"] == "file")
        # calculate total storage size
        total_size = 0
        for entry in index.values():
            try:
                if os.path.exists(entry["file_path"]):
                    total_size += os.path.getsize(entry["file_path"])
            except:
                pass
        #get peer statistics
        peer_stats = {}
        for entry in index.values():
            peer_name = entry["peer_name"]
            if peer_name not in peer_stats:
                peer_stats[peer_name] = {"text": 0, "file": 0}
            peer_stats[peer_name][entry["message_type"]] += 1
        return {
            "total_messages": total_messages,
            "text_messages": text_messages,
            "file_messages": file_messages,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "peer_statistics": peer_stats,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    def cleanup_old_messages(self, days_old: int = 30) -> int:
        """removing messages older than specified days"""
        index = self._load_message_index()
        cutoff_date = datetime.now(timezone.utc).timestamp() - (days_old * 24 * 3600)
        messages_to_delete = []
        for message_id, entry in index.items():
            try:
                stored_at = datetime.fromisoformat(entry["stored_at"].replace('Z', '+00:00'))
                if stored_at.timestamp() < cutoff_date:
                    messages_to_delete.append(message_id)
            except:
                continue
        deleted_count = 0
        for message_id in messages_to_delete:
            if self.delete_message(message_id):
                deleted_count += 1
        print(f"Cleaned up {deleted_count} old messages")
        return deleted_count
    
    def _generate_message_id(self, message_packet: Dict[str, Any]) -> str:
        """generate unique message ID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"{message_packet.get('from', '')}{message_packet.get('to', '')}{timestamp}"
        return base64.b64encode(data.encode()).decode()[:16]
    
    def _safe_filename(self, filename: str) -> str:
        """create safe filname"""
        import re
        safe = re.sub(r'[^\w\-_\.]', '_', filename)
        return safe[:100]
    
    def update_message_index(
            self, 
            message_id: str, 
            file_path: str, 
            peer_name: str, 
            message_type: str, 
            filename: str |None=None):
        """update the message index"""
        index = self._load_message_index()
        index[message_id] = {
            "message_id": message_id,
            "file_path": file_path,
            "peer_name": peer_name,
            "message_type": message_type,
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "filename": filename
        }
        self._save_message_index(index)

    def _load_message_index(self) -> Dict[str, Any]:
        """load message index from file"""
        index_file = os.path.join(self.encrypted_dir, "message_index.json")
        if not os.path.exists(index_file):
            return {}
        try:
            with open(index_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_message_index(self, index: Dict[str, Any]):
        """save message index to file"""
        index_file = os.path.join(self.encrypted_dir, "message_index.json")
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)

class CompactMessageStore:
    """alt storage system using MessagePack for compact binary storage"""
    def __init__(self, encrypted_dir: str = "encrypted"):
        self.encrypted_dir = encrypted_dir
        self.compact_dir = os.path.join(encrypted_dir, "compact")
        self.ensure_directories()
    def ensure_directories(self):
        """createion of compact storage directory"""
        if not os.path.exists(self.compact_dir):
            os.makedirs(self.compact_dir)
    def save_message_compact(self, message_packet: Dict[str, Any], peer_name: str) -> str:
        """save message using MessagePack (binary, compact)"""
        message_id = message_packet.get("message_id", self._generate_message_id(message_packet))
        # create compact storage data
        compact_data = {
            "id": message_id,
            "peer": peer_name,
            "stored": datetime.now(timezone.utc).timestamp(),
            "packet": message_packet
        }
        # save using MessagePack
        filename = f"{peer_name}_{message_id[:8]}.msgpack"
        file_path = os.path.join(self.compact_dir, filename)
        with open(file_path, 'wb') as f:
            msgpack.dump(compact_data, f)
        print(f"Compact message saved: {file_path}")
        return message_id
    
    def load_message_compact(self, message_id: str, peer_name: str) -> Optional[Dict[str, Any]]:
        """load message from compact storage"""
        filename = f"{peer_name}_{message_id[:8]}.msgpack"
        file_path = os.path.join(self.compact_dir, filename)
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, 'rb') as f:
                result = msgpack.load(f, raw=False)
            if isinstance(result, dict):
                return result
            else:
                return None
        except:
            return None
    
    def _generate_message_id(self, message_packet: Dict[str, Any]) -> str:
        """generation of unique message ID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        data = f"{message_packet.get('from', '')}{message_packet.get('to', '')}{timestamp}"
        return base64.b64encode(data.encode()).decode()[:16]

# use cases functionings
def create_message_store(encrypted_dir: str = "encrypted") -> MessageStore:
    """create a new message store"""
    return MessageStore(encrypted_dir)

def backup_messages(store: MessageStore, backup_path: str) -> bool:
    """create backup of all messages"""
    try:
        import shutil
        shutil.copytree(store.encrypted_dir, backup_path)
        print(f"Messages backed up to: {backup_path}")
        return True
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

if __name__ == "__main__":
    # test the message store
    print("Testing Message Store...")
    store = create_message_store()
    # test message packet
    test_packet = {
        "from": "Alice",
        "to": "Bob",
        "message_id": "test123",
        "encrypted_data": {
            "ciphertext": "dGVzdCBjaXBoZXJ0ZXh0",
            "nonce": "dGVzdCBub25jZQ==",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "algorithm": "XChaCha20-Poly1305"
        }
    }
    # save this message
    message_id = store.save_message(test_packet, "Bob")
    # load this message
    loaded = store.load_message(message_id)
    print(f"Message saved and loaded successfully: {loaded is not None}")
    # get me statistics
    stats = store.get_storage_stats()
    print(f"Storage stats: {stats}")