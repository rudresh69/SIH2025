// frontend/src/components/ModelPredictions.tsx
import React from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

interface ModelPredictionsProps {
  triggerAlert?: boolean;
}

// --- CHANGE: Define a type for expected WebSocket data
interface WsData {
  prediction?: 'Event Detected' | 'Normal';
  confidence?: number;
  weather_forecast?: [number, number, number][]; // [rain, temp, hum]
}

const ModelPredictions: React.FC<ModelPredictionsProps> = ({ triggerAlert = false }) => {
  const { data } = useWebSocket<WsData>();

  // --- CHANGE: Derive values from live data or the manual alert trigger
  const isEventPredicted = data?.prediction === 'Event Detected';
  const sensorRisk = triggerAlert ? 95 : (isEventPredicted ? (data?.confidence ?? 0) * 100 : (data?.confidence ?? 0) * 50);

  const avgRainfall = data?.weather_forecast?.[0]?.[0] ?? 0; // Rain from first forecast step
  let weatherRisk: 'Low' | 'Medium' | 'High' = 'Low';
  if (triggerAlert || avgRainfall > 10) weatherRisk = 'High';
  else if (avgRainfall > 2) weatherRisk = 'Medium';
  
  const imageRisk: 'Normal' | 'Warning' | 'Rockfall' = triggerAlert || sensorRisk > 80 ? 'Rockfall' : sensorRisk > 50 ? 'Warning' : 'Normal';

  const getRiskColor = (risk: number | string) => {
    if (typeof risk === 'string') {
        if (risk === 'Low' || risk === 'Normal') return 'text-green-500';
        if (risk === 'Medium' || risk === 'Warning') return 'text-orange-500';
        return 'text-red-500';
    }
    if (risk < 30) return 'text-green-500';
    if (risk < 70) return 'text-orange-500';
    return 'text-red-500';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg mb-4">
      {/* Sensor Risk */}
      <div className="bg-white p-4 rounded-lg shadow text-center">
        <h3 className="text-lg font-semibold mb-2 text-gray-700">Sensor Risk (AI Model)</h3>
        <p className={`text-5xl font-bold ${getRiskColor(sensorRisk)}`}>{sensorRisk.toFixed(0)}%</p>
        <p className={`font-semibold mt-2 ${getRiskColor(sensorRisk)}`}>
            {sensorRisk < 30 ? 'Normal' : sensorRisk < 70 ? 'Warning' : 'High Risk'}
        </p>
      </div>

      {/* Weather Risk */}
      <div className="bg-white p-4 rounded-lg shadow text-center">
        <h3 className="text-lg font-semibold mb-2 text-gray-700">Weather Risk</h3>
        <p className={`text-5xl font-bold ${getRiskColor(weatherRisk)}`}>{weatherRisk}</p>
        <p className={`font-semibold mt-2 ${getRiskColor(weatherRisk)}`}>
            {weatherRisk === 'Low' ? 'Safe Conditions' : weatherRisk === 'Medium' ? 'Caution Advised' : 'Dangerous Conditions'}
        </p>
      </div>

      {/* Image Risk */}
      <div className="bg-white p-4 rounded-lg shadow text-center">
        <h3 className="text-lg font-semibold mb-2 text-gray-700">Image Risk (Camera)</h3>
        <p className={`text-5xl font-bold ${getRiskColor(imageRisk)}`}>{imageRisk}</p>
        <p className={`font-semibold mt-2 ${getRiskColor(imageRisk)}`}>
            {imageRisk === 'Normal' ? 'No Issues Detected' : imageRisk === 'Warning' ? 'Possible Issues' : 'Critical Issues'}
        </p>
      </div>
    </div>
  );
};

export default ModelPredictions;