/**
 * Main Entry Point
 * Ephemeral Intent Synthesis System
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import { validateConfig } from './config';

// Validate configuration before starting
if (!validateConfig()) {
  console.error('Invalid configuration. Please check your environment variables.');
}

// Render app
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Made with Bob for IBM AI Builders Challenge