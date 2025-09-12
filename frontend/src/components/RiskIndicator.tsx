import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

// An updated interface for the data we expect from the WebSocket
type WsData = {
  prediction?: 'Normal' | 'Event Detected' | null;
  confidence?: number;
  weather_forecast?: any;
  event_phase?: 'none' | 'early_warning' | 'main_event';
};

const RiskIndicator: React.FC<{ triggerAlert?: boolean }> = ({ triggerAlert = false }) => {
  const { data } = useWebSocket<WsData>();
  const [risk, setRisk] = useState<'safe' | 'caution' | 'danger'>('safe');

  useEffect(() => {
    let newRisk: 'safe' | 'caution' | 'danger' = 'safe';

    // Rule 1 (Lowest Priority): Check for weather-related caution
    if (data?.weather_forecast) {
      const wf = data.weather_forecast;
      if (Array.isArray(wf) && wf.length > 0) {
        const rain = Number(wf[0]?.[0] ?? 0);
        if (rain > 2) newRisk = 'caution'; // Heavy rain forecast raises caution
      }
    }

    // Rule 2: Check the ML model's confidence for a higher level of risk
    if (data?.prediction === 'Event Detected') {
      const confidence = data.confidence ?? 0;
      if (confidence > 0.5) newRisk = 'caution';
      if (confidence > 0.8) newRisk = 'danger'; // High confidence prediction raises danger
    }
    
    // Rule 3 (High Priority): Check for an official event phase from the backend
    if (data?.event_phase === 'early_warning' || data?.event_phase === 'main_event') {
      newRisk = 'danger';
    }

    // Rule 4 (Highest Priority): Manual override for the demo button
    if (triggerAlert) {
      newRisk = 'danger';
    }

    setRisk(newRisk);
  }, [data, triggerAlert]);

  const color =
    risk === 'safe' ? 'bg-green-500' : risk === 'caution' ? 'bg-orange-500' : 'bg-red-500';
  const text = risk === 'safe' ? 'SAFE' : risk === 'caution' ? 'CAUTION' : 'DANGER';
  const icon = risk === 'safe' ? '✅' : risk === 'caution' ? '⚠️' : '🚨';

  return (
    <div className="bg-white p-4 rounded-lg shadow h-full">
      <h3 className="text-lg font-semibold mb-4">Final Risk Indicator</h3>
      <div className={`${color} rounded-lg p-6 text-white text-center flex flex-col justify-center items-center h-48 transition-colors duration-500`}>
        <div className="text-6xl mb-2">{icon}</div>
        <div className="text-4xl font-bold tracking-wider">{text}</div>
      </div>
    </div>
  );
};

export default RiskIndicator;