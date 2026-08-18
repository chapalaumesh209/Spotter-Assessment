import React from 'react';

const LoadingOverlay: React.FC = () => {
  return (
    <div className="loading-overlay">
      <div className="loading-content">
        <div className="spinner"></div>
        <p className="loading-text">Calculating optimal route...</p>
      </div>
    </div>
  );
};

export default LoadingOverlay;
