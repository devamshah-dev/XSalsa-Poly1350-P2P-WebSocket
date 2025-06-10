import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// API client of WebSocket backend
function useP2PWebSocket(url) {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket(url);

    ws.current.onopen = () => setIsConnected(true);
    ws.current.onclose = () => setIsConnected(false);

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      // handle server messages
      if (message.type === 'new_message') {
        setMessages(prev => [...prev, message.data]);
      } else if (message.type === 'response' && message.action === 'get_history') {
        // replace messages with history
        if (message.data.success) {
            setMessages(message.data.history);
        }
      }
    };

    return () => {
      ws.current.close();
    };
  }, [url]);

  const sendCommand = (action, payload) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action, payload }));
    }
  };

  return { messages, isConnected, sendCommand, setMessages };
}


function App() {
  const [peerName, setPeerName] = useState('');
  const [chattingWith, setChattingWith] = useState('');
  const [messageInput, setMessageInput] = useState('');
  const { messages, isConnected, sendCommand, setMessages } = useP2PWebSocket('ws://localhost:8765');
  const messagesEndRef = useRef(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  const handleCreatePeer = (e) => {
    e.preventDefault();
    if (!peerName) return;
    sendCommand('create_peer', { name: peerName });
    alert(`Request to create peer '${peerName}' sent.`);
  };

  const handleStartChat = (e) => {
    e.preventDefault();
    if (!peerName || !chattingWith) return;
    // ensure other peer exists
    sendCommand('create_peer', { name: chattingWith });
    // connect them
    sendCommand('connect_peers', { peer1: peerName, peer2: chattingWith });
    // fetch history
    sendCommand('get_history', { peer_a: peerName, peer_b: chattingWith });
    alert(`Attempting to start chat with '${chattingWith}'.`);
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!messageInput || !peerName || !chattingWith) return;
    sendCommand('send_message', { from: peerName, to: chattingWith, message: messageInput });
    // add message to the UI
    setMessages(prev => [...prev, { from: peerName, to: chattingWith, message: messageInput, timestamp: new Date().toISOString() }]);
    setMessageInput('');
  };


  return (
    <div className="App">
      <header className="App-header">
        <h1>P2P Encrypted Chat (XChaCha20)</h1>
        <p>Status: <span className={isConnected ? 'connected' : 'disconnected'}>{isConnected ? 'Connected' : 'Disconnected'}</span></p>
      </header>
      <div className="main-content">
        <div className="setup-panel">
          <h2>Setup</h2>
          <form onSubmit={handleCreatePeer}>
            <input
              type="text"
              placeholder="Your Peer Name (e.g., Alice)"
              value={peerName}
              onChange={(e) => setPeerName(e.target.value)}
            />
            <button type="submit">Create My Peer</button>
          </form>
          <form onSubmit={handleStartChat}>
            <input
              type="text"
              placeholder="Chat With Peer (e.g., Bob)"
              value={chattingWith}
              onChange={(e) => setChattingWith(e.target.value)}
            />
            <button type="submit" disabled={!peerName}>Start Chat</button>
          </form>
        </div>

        <div className="chat-panel">
          <h2>Chat with: {chattingWith || '...'}</h2>
          <div className="message-area">
            {messages.filter(m => 
                (m.from === peerName && m.to === chattingWith) || 
                (m.from === chattingWith && m.to === peerName)
              ).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
              .map((msg, index) => (
              <div key={index} className={`message ${msg.from === peerName ? 'sent' : 'received'}`}>
                <strong>{msg.from}:</strong> {msg.message}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          <form className="message-input-form" onSubmit={handleSendMessage}>
            <input
              type="text"
              placeholder="Type your secure message..."
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              disabled={!peerName || !chattingWith}
            />
            <button type="submit" disabled={!peerName || !chattingWith}>Send</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;