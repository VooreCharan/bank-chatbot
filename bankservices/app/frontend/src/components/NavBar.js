import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/NavBar.scss';

const NavBar = () => {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="bank-icon">
            <path d="M3 21H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M5 21V7L12 3L19 7V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M9 21V15H15V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span>Chase AI Assistant</span>
        </Link>
        
        <div className="navbar-links">
          <a href="https://www.chase.com" target="_blank" rel="noopener noreferrer" className="nav-link">
            Chase Website
          </a>
        </div>
      </div>
    </nav>
  );
};

export default NavBar;