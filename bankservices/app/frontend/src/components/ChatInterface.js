import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import ChatMessage from './ChatMessage';
import LoadingIndicator from './LoadingIndicator';
import '../styles/ChatInterface.scss';

const API_URL = 'http://localhost:5000/api/chat';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => {
    // Get stored user ID or create a new one
    const storedId = localStorage.getItem('chatbot_user_id');
    if (storedId) return storedId;
    
    const newId = uuidv4();
    localStorage.setItem('chatbot_user_id', newId);
    return newId;
  });
  
  const messagesEndRef = useRef(null);
  
  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // Add welcome message on first load
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          text: "Hello! I'm your Chase Bank assistant. How can I help you today?",
          sender: 'bot',
          timestamp: new Date()
        }
      ]);
    }
  }, [messages.length]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    const userMessage = {
      id: uuidv4(),
      text: input,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      const response = await axios.post(API_URL, {
        user_id: userId,
        message: input
      });
      
      const { answer, context, has_memory } = response.data;
      
      const botMessage = {
        id: uuidv4(),
        text: answer,
        sender: 'bot',
        context: context,
        hasMemory: has_memory,
        timestamp: new Date()
      };
      
      // Add slight delay for better UX
      setTimeout(() => {
        setMessages(prevMessages => [...prevMessages, botMessage]);
        setIsLoading(false);
      }, 500);
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage = {
        id: uuidv4(),
        text: "I'm sorry, I couldn't process your request at the moment. Please try again later.",
        sender: 'bot',
        isError: true,
        timestamp: new Date()
      };
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
      setIsLoading(false);
    }
  };
  
  const handleClearChat = () => {
    setMessages([
      {
        id: 'welcome-new',
        text: "Chat history cleared! I still remember our previous conversations. How else can I help you today?",
        sender: 'bot',
        timestamp: new Date()
      }
    ]);
  };
  
  const suggestedQuestions = [
    "What are the fees for international transactions?",
    "How do I check my account balance?",
    "What are the steps to reset my password?",
    "Tell me about loan interest rates.",
    "How do I open a new account?",
    "How can I view my recent transactions?",
    "Where can I find my account details?",
    "What are Chase's banking policies?",
    "How do I manage my account settings?",
    "How do I transfer funds between accounts?"
  ];

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Chase Bank Assistant</h2>
        <button className="clear-button" onClick={handleClearChat}>
          Clear Chat
        </button>
      </div>
      
      <div className="messages-container">
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {isLoading && <LoadingIndicator />}
        <div ref={messagesEndRef} />
      </div>
      
      {messages.length <= 2 && (
        <div className="suggested-questions">
          <p>Try asking:</p>
          <div className="questions-grid">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => {
                  setInput(question);
                  // Allow time for the input to update before submitting
                  setTimeout(() => {
                    const form = document.querySelector('.chat-input-form');
                    if (form) form.dispatchEvent(new Event('submit', { cancelable: true }));
                  }, 10);
                }}
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}
      
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your banking question here..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;