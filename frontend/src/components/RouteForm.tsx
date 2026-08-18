import React, { useState } from 'react';

interface RouteFormProps {
  onSubmit: (start: string, finish: string) => void;
  isLoading: boolean;
}

const RouteForm: React.FC<RouteFormProps> = ({ onSubmit, isLoading }) => {
  const [start, setStart] = useState('');
  const [finish, setFinish] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!start.trim() || !finish.trim()) {
      setError('Both start and finish locations are required.');
      return;
    }

    onSubmit(start, finish);
  };

  return (
    <form className="route-form" onSubmit={handleSubmit}>
      <div className="route-form__inputs">
        <div className="route-form__group">
          <label htmlFor="start" className="route-form__label">Start Location</label>
          <input
            id="start"
            type="text"
            className="route-form__input"
            placeholder="e.g., New York, NY"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            disabled={isLoading}
          />
        </div>
        <div className="route-form__group">
          <label htmlFor="finish" className="route-form__label">Finish Location</label>
          <input
            id="finish"
            type="text"
            className="route-form__input"
            placeholder="e.g., Los Angeles, CA"
            value={finish}
            onChange={(e) => setFinish(e.target.value)}
            disabled={isLoading}
          />
        </div>
      </div>
      {error && <div className="route-form__error">{error}</div>}
      <button type="submit" className="route-form__button" disabled={isLoading}>
        {isLoading ? (
          <span className="route-form__spinner"></span>
        ) : (
          'Calculate Route'
        )}
      </button>
    </form>
  );
};

export default RouteForm;
