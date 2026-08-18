import React from 'react';
import { RouteResponse } from '../types';

interface ResultsCardsProps {
  data: RouteResponse;
}

const ResultsCards: React.FC<ResultsCardsProps> = ({ data }) => {
  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  return (
    <div className="results-cards">
      <div className="card">
        <div className="card__icon">🛣️</div>
        <div className="card__value">{data.route.distance_miles.toFixed(1)}</div>
        <div className="card__label">Total Distance (miles)</div>
      </div>
      <div className="card">
        <div className="card__icon">⏱️</div>
        <div className="card__value">{formatDuration(data.route.duration_minutes)}</div>
        <div className="card__label">Drive Time</div>
      </div>
      <div className="card">
        <div className="card__icon">⛽</div>
        <div className="card__value">{data.fuel.total_fuel_consumed.toFixed(1)}</div>
        <div className="card__label">Fuel Consumed (gal)</div>
      </div>
      <div className="card">
        <div className="card__icon">💲</div>
        <div className="card__value">${data.fuel.total_cost.toFixed(2)}</div>
        <div className="card__label">Total Fuel Cost</div>
      </div>
      <div className="card">
        <div className="card__icon">🛑</div>
        <div className="card__value">{data.fuel_stops.length}</div>
        <div className="card__label">Fuel Stops</div>
      </div>
    </div>
  );
};

export default ResultsCards;
