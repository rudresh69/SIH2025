import React, { useEffect, useRef, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

type WsData = {
  timestamp: string;
  prediction?: string | null;
  label?: number;
  weather_forecast?: any[];
  event_phase?: 'none' | 'normal' | 'warning' | 'danger' | 'main_event';
  event_active?: boolean;
  event_type?: string;
};

type LogEntry = { timestamp: string; message: string; level: 'info' | 'warning' | 'danger' };

const formatTS = (iso?: string) => {
  try {
    if (!iso) return new Date().toLocaleTimeString();
    return iso.slice(11, 19);
  } catch {
    return new Date().toLocaleTimeString();
  }
};

const EventLog: React.FC<{ triggerAlert?: boolean }> = ({ triggerAlert = false }) => {
  const { data } = useWebSocket<WsData>();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  
  const lastPredictionRef = useRef<string | null>(null);
  const lastEventPhaseRef = useRef<string>('none');
  // --- CHANGE: Add a ref to track the rain alert status ---
  const isHeavyRainAlertActiveRef = useRef<boolean>(false);

  const push = (message: string, level: LogEntry['level']) => {
    setLogs(prev => [{ timestamp: new Date().toISOString(), message, level }, ...prev].slice(0, 200));
  };

  useEffect(() => {
    push('System initialized and connected.', 'info');
    const interval = setInterval(() => {
      push('Receiving normal readings - All systems operational', 'info');
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!data) return;
    const ts = formatTS(data.timestamp);

    const currentPhase = data.event_phase ?? 'none';
    const eventType = data.event_type ?? 'event';
    if (currentPhase !== lastEventPhaseRef.current) {
      switch (currentPhase) {
        case 'normal':
          push(`[${ts}] EVENT START: Receiving normal readings - All systems operational`, 'info');
          break;
        case 'warning':
          push(`[${ts}] WARNING: Receiving unusual readings - Potential ${eventType} detected`, 'warning');
          break;
        case 'danger':
          push(`[${ts}] DANGER: Evacuate immediately - ${eventType.charAt(0).toUpperCase() + eventType.slice(1)} imminent! Audio alert activated!`, 'danger');
          break;
        case 'main_event':
          push(`[${ts}] EMERGENCY: ${eventType.charAt(0).toUpperCase() + eventType.slice(1)} in progress - Take cover!`, 'danger');
          break;
        case 'none':
          if (lastEventPhaseRef.current !== 'none') {
            push(`[${ts}] EVENT END: System returning to normal state - Receiving normal readings`, 'info');
          }
          break;
      }
      lastEventPhaseRef.current = currentPhase;
    }

    const pred = data.prediction ?? null;
    if (pred && pred !== lastPredictionRef.current) {
      const lvl = pred === 'Event Detected' ? 'danger' : 'info';
      push(`[${ts}] Model Prediction updated to: ${pred}`, lvl);
      lastPredictionRef.current = pred;
    }

    // --- CHANGE: Updated weather logic to only log on state change ---
    if (Array.isArray(data.weather_forecast) && data.weather_forecast.length > 0) {
      const rain = Number(data.weather_forecast[0]?.[0] ?? 0);
      const isHeavyRainNow = rain > 10;

      // Log only when heavy rain *starts*
      if (isHeavyRainNow && !isHeavyRainAlertActiveRef.current) {
        push(`[${ts}] Weather Alert: Heavy rain forecasted (${rain.toFixed(1)} mm/hr)`, 'warning');
        isHeavyRainAlertActiveRef.current = true;
      } 
      // Log only when heavy rain *stops*
      else if (!isHeavyRainNow && isHeavyRainAlertActiveRef.current) {
        push(`[${ts}] Weather Update: Rainfall has subsided.`, 'info');
        isHeavyRainAlertActiveRef.current = false;
      }
    }
  }, [data]);

  useEffect(() => {
    if (triggerAlert) {
      push('Frontend event trigger button clicked.', 'info');
    }
  }, [triggerAlert]);

  return (
    <div className="bg-white p-4 rounded-lg shadow h-full">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">Event Log</h3>
      <div className="h-96 overflow-y-auto border border-gray-200 rounded p-3 bg-gray-50 font-mono text-sm">
        {logs.map((l, idx) => (
          <div key={idx} className={`mb-1 flex`}>
            <span className="text-gray-400 mr-3">[{formatTS(l.timestamp)}]</span>
            <span className={`${l.level === 'danger' ? 'text-red-600 font-bold' : l.level === 'warning' ? 'text-orange-500' : 'text-blue-700'}`}>
              {l.message.replace(/\[.*?\]\s/, '')}
            </span>
          </div>
        ))}
        {logs.length === 0 && (
          <div className="text-gray-400 italic">No events recorded yet...</div>
        )}
      </div>
    </div>
  );
};

export default EventLog;