import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { RouteResponse } from '../types';

// Configure Leaflet default icons using reliable CDN URLs
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

interface RouteMapProps {
  data: RouteResponse;
}

// Component to auto-fit the map bounds to the route
const MapBounds: React.FC<{ positions: [number, number][] }> = ({ positions }) => {
  const map = useMap();
  useEffect(() => {
    if (positions.length > 0) {
      const bounds = L.latLngBounds(positions);
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, positions]);
  return null;
};

const RouteMap: React.FC<RouteMapProps> = ({ data }) => {
  // Convert GeoJSON [lng, lat] to Leaflet [lat, lng]
  const positions: [number, number][] = data.route.geometry.coordinates.map(
    (coord) => [coord[1], coord[0]] as [number, number]
  );

  const startPos: [number, number] = [data.start.latitude, data.start.longitude];
  const finishPos: [number, number] = [data.finish.latitude, data.finish.longitude];

  // Custom marker icons
  const createIcon = (color: string) => {
    return L.divIcon({
      className: 'custom-div-icon',
      html: `<div style="background-color:${color};width:16px;height:16px;border-radius:50%;border:2px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);"></div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    });
  };

  const startIcon = createIcon('#2d6a4f');
  const finishIcon = createIcon('#dc3545');
  const fuelIcon = createIcon('#e67e22');

  return (
    <div className="route-map-container">
      <MapContainer
        bounds={positions.length > 0 ? L.latLngBounds(positions) : undefined}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {positions.length > 0 && (
          <>
            <Polyline positions={positions} color="#2d6a4f" weight={5} opacity={0.8} />
            <MapBounds positions={positions} />
          </>
        )}
        
        <Marker position={startPos} icon={startIcon}>
          <Popup>
            <strong>Start:</strong> {data.start.address}
          </Popup>
        </Marker>

        <Marker position={finishPos} icon={finishIcon}>
          <Popup>
            <strong>Finish:</strong> {data.finish.address}
          </Popup>
        </Marker>

        {data.fuel_stops.map((stop, index) => (
          <Marker
            key={index}
            position={[stop.latitude, stop.longitude]}
            icon={fuelIcon}
          >
            <Popup className="fuel-popup">
              <strong>{stop.station_name}</strong><br/>
              {stop.address}, {stop.city}, {stop.state}<br/>
              Price: ${stop.price_per_gallon.toFixed(2)} / gal<br/>
              Gallons: {stop.gallons_purchased.toFixed(1)}<br/>
              Cost: ${stop.cost.toFixed(2)}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};

export default RouteMap;
