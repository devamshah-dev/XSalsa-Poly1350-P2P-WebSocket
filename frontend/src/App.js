import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// api client of webSocket backend --> slow my pc
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
      if (message.type === 'new_message') {
        setMessages(prev => [...prev, message.data]);
      } else if (message.type === 'response' && message.action === 'get_history') {
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
  // localStorage setup here.
   const getInitialState = () => {
    const urlParams = new URLSearchParams(window.location.search);
    const peerFromUrl = urlParams.get('peer');
    const chatWithFromUrl = urlParams.get('chatWith');

    if (peerFromUrl) {
      //use URL specified peer.
      return {
        peerName: peerFromUrl,
        chattingWith: chatWithFromUrl || ''
      };
    } else {
      // else, fallback to localStorage.
      return {
        peerName: localStorage.getItem('p2p-peerName') || '',
        chattingWith: localStorage.getItem('p2p-chattingWith') || ''
      };
    }
  };
  const initialState = getInitialState();
  const [peerName, setPeerName] = useState(() => localStorage.getItem('p2p-peerName') || '');
  const [chattingPeer, setchattingPeer] = useState(() => localStorage.getItem('p2p-chattingPeer') || '');
  const [messageInput, setMessageInput] = useState('');
  const { messages, isConnected, sendCommand, setMessages } = useP2PWebSocket('ws://localhost:8765');
  const messagesEndRef = useRef(null);

  // save state changes in localStorage
  useEffect(() => {
    // update on `peerName` change --> issue with Firefox.
    if (peerName) {
      localStorage.setItem('p2p-peerName', peerName);
    } else {
      // peerName removed from storage.
      localStorage.removeItem('p2p-peerName');
    }
  }, [peerName]);

  // change chattingPeer state
  useEffect(() => {
    // chattingPeer changes.
    if (chattingPeer) {
      localStorage.setItem('p2p-chattingPeer', chattingPeer);
    } else {
      localStorage.removeItem('p2p-chattingPeer');
    }
  }, [chattingPeer]);


  // set up the peer on page load if the info exists auto.
  useEffect(() => {
    if (peerName && isConnected) {
      // bbackend connect to peer from localStorage.
      sendCommand('create_peer', { name: peerName });

      if (chattingPeer) {
        // re-establish the connection.
        sendCommand('create_peer', { name: chattingPeer });
        sendCommand('connect_peers', { peer1: peerName, peer2: chattingPeer });
        sendCommand('get_history', { peer_a: peerName, peer_b: chattingPeer });
      }
    }
  }, [peerName, chattingPeer, isConnected, sendCommand]);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!messageInput || !peerName || !chattingPeer) return;
    sendCommand('send_message', { from: peerName, to: chattingPeer, message: messageInput });
    setMessages(prev => [...prev, { from: peerName, to: chattingPeer, message: messageInput, timestamp: new Date().toISOString() }]);
    setMessageInput('');
  };

  // function to clear stored identity
  const handleClearIdentity = () => {
    // clear React state
    setPeerName('');
    setchattingPeer('');
    // clear localStorage
    localStorage.removeItem('p2p-peerName');
    localStorage.removeItem('p2p-chattingPeer');
    setMessages([]);
    alert('This peer identity is cleared now.');
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>P2P Encrypted Chat Service</h1>
         {peerName && <h2>My Identity: <span className="peer-identity">{peerName}</span></h2>}
        <p>Status: <span className={isConnected ? 'connected' : 'disconnected'}>{isConnected ? 'Connected' : 'Disconnected'}</span></p>
      </header>

      <div className="main-content">
        <div className="chat-panel full-width">
          <h2>Chat with: <span className="peer-identity">{chattingWith || '...'}</span></h2>
          <div className="message-area">
            {messages.filter(m => 
                (m.from === peerName && m.to === chattingPeer) || 
                (m.from === chattingPeer && m.to === peerName)
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
              placeholder="Enter message..."
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              disabled={!peerName || !chattingPeer}
            />
            <button type="submit" disabled={!peerName || !chattingPeer}>Send</button>
          </form>
        </div>
      </div>
    </div>
  );
}
export default App;