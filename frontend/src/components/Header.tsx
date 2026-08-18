import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header__container">
        <h1 className="header__title">Fuel-Optimal Route Planner</h1>
        <p className="header__subtitle">Find the most cost-effective fuel stops along a US driving route.</p>
      </div>
    </header>
  );
};

export default Header;
