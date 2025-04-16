import React from 'react';
import '../styles/LoadingIndicator.scss';

const LoadingIndicator = () => {
  return (
    <div className="loading-container">
      <div className="loading-avatar">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2L14.8 8.8L22 10L17 15L18.2 22L12 18.8L5.8 22L7 15L2 10L9.2 8.8L12 2Z" stroke="currentColor" fill="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
      
      <div className="loading-content">
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
};

export default LoadingIndicator;