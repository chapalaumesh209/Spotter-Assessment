import React from 'react';
import { RouteResponse } from '../types';

interface FuelStopTableProps {
  data: RouteResponse;
}

const FuelStopTable: React.FC<FuelStopTableProps> = ({ data }) => {
  if (!data.fuel_stops || data.fuel_stops.length === 0) {
    return <div className="fuel-table-empty">No fuel stops needed for this route.</div>;
  }

  // Find the cheapest stop
  const cheapestPrice = Math.min(...data.fuel_stops.map(s => s.price_per_gallon));

  return (
    <div className="fuel-table-container">
      <h3 className="fuel-table-title">Fuel Stop Details</h3>
      <div className="table-responsive">
        <table className="fuel-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Station</th>
              <th>Location</th>
              <th>Price/Gal</th>
              <th>Route Mile</th>
              <th>Gallons</th>
              <th>Cost</th>
            </tr>
          </thead>
          <tbody>
            {data.fuel_stops.map((stop, index) => {
              const isCheapest = stop.price_per_gallon === cheapestPrice;
              return (
                <tr key={index} className={isCheapest ? 'row-cheapest' : ''}>
                  <td>{index + 1}</td>
                  <td className="station-name">{stop.station_name}</td>
                  <td>{stop.city}, {stop.state}</td>
                  <td className={isCheapest ? 'text-highlight' : ''}>${stop.price_per_gallon.toFixed(2)}</td>
                  <td>{stop.route_mile.toFixed(1)}</td>
                  <td>{stop.gallons_purchased.toFixed(1)}</td>
                  <td className="text-bold">${stop.cost.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={5} className="text-right"><strong>Total:</strong></td>
              <td><strong>{data.fuel.total_gallons_purchased.toFixed(1)} gal</strong></td>
              <td className="text-bold text-total"><strong>${data.fuel.total_cost.toFixed(2)}</strong></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
};

export default FuelStopTable;
