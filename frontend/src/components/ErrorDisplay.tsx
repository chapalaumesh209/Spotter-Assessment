import React from 'react';

interface ErrorDisplayProps {
  message: string;
  onDismiss: () => void;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ message, onDismiss }) => {
  if (!message) return null;

  return (
    <div className="error-display">
      <div className="error-content">
        <span className="error-icon">⚠️</span>
        <span className="error-message">{message}</span>
      </div>
      <button className="error-dismiss" onClick={onDismiss} aria-label="Dismiss error">
        &times;
      </button>
    </div>
  );
};

export default ErrorDisplay;
