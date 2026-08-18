import React, { useState } from 'react';
import Header from './components/Header';
import RouteForm from './components/RouteForm';
import ResultsCards from './components/ResultsCards';
import RouteMap from './components/RouteMap';
import FuelStopTable from './components/FuelStopTable';
import LoadingOverlay from './components/LoadingOverlay';
import ErrorDisplay from './components/ErrorDisplay';
import { calculateRoute } from './services/api';
import { RouteResponse } from './types';
import './App.css';

const App: React.FC = () => {
  const [routeData, setRouteData] = useState<RouteResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCalculateRoute = async (start: string, finish: string) => {
    setIsLoading(true);
    setError('');
    setRouteData(null);
    
    try {
      const data = await calculateRoute(start, finish);
      setRouteData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to calculate route. Please check your locations and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <Header />
      
      <main className="main-content">
        <div className="container">
          {error && <ErrorDisplay message={error} onDismiss={() => setError('')} />}
          
          <div className="form-section">
            <RouteForm onSubmit={handleCalculateRoute} isLoading={isLoading} />
          </div>

          {routeData && (
            <div className="results-section fade-in">
              <ResultsCards data={routeData} />
              <RouteMap data={routeData} />
              <FuelStopTable data={routeData} />
            </div>
          )}
        </div>
      </main>

      {isLoading && <LoadingOverlay />}
    </div>
  );
};

export default App;
