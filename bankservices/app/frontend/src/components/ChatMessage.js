import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import '../styles/ChatMessage.scss';

const ChatMessage = ({ message }) => {
  const messageRef = useRef(null);
  
  useEffect(() => {
    // Animation for new messages
    if (messageRef.current) {
      gsap.fromTo(
        messageRef.current,
        { 
          opacity: 0, 
          y: 20 
        },
        { 
          opacity: 1, 
          y: 0, 
          duration: 0.5,
          ease: "power2.out"
        }
      );
    }
  }, []);
  
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  const { text, sender, timestamp, context, hasMemory, isError } = message;
  
  return (
    <div 
      ref={messageRef}
      className={`message ${sender === 'user' ? 'user-message' : 'bot-message'} ${isError ? 'error-message' : ''}`}
    >
      <div className="message-avatar">
        {sender === 'user' ? (
          <div className="user-avatar">
            <span>U</span>
          </div>
        ) : (
          <div className="bot-avatar">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L14.8 8.8L22 10L17 15L18.2 22L12 18.8L5.8 22L7 15L2 10L9.2 8.8L12 2Z" stroke="currentColor" fill="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
        )}
      </div>
      
      <div className="message-content">
        <div className="message-text">
          {text}
          
          {sender === 'bot' && context && !isError && (
            <div className="message-context">
              <span className="context-source">
                Source: {context}
                {hasMemory && <span className="memory-badge">Memory Used</span>}
              </span>
            </div>
          )}
        </div>
        
        <div className="message-time">
          {formatTime(timestamp)}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;