import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

interface AlertData {
  timestamp: string;
  prediction?: string | null;
  confidence?: number;
  event_active: boolean;
  event_phase?: string;
}

const AlertPanel: React.FC = () => {
  const { data, isConnected } = useWebSocket<AlertData>();
  const [alertLevel, setAlertLevel] = useState<string>('normal');
  const [prediction, setPrediction] = useState<number>(0);
  const [eventActive, setEventActive] = useState<boolean>(false);
  const [eventPhase, setEventPhase] = useState<string>('');
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    if (data) {
      const { prediction, confidence, event_active, event_phase, timestamp } = data;
      setPrediction(confidence || 0);
      setEventActive(event_active);
      setEventPhase(event_phase || '');
      setLastUpdate(timestamp.slice(11, 19));

      // Determine alert level based on prediction and confidence
      if (event_active && event_phase === 'main_event') {
        setAlertLevel('critical');
      } else if (event_active && event_phase === 'danger') {
        setAlertLevel('critical');
      } else if (event_active && event_phase === 'warning') {
        setAlertLevel('warning');
      } else if (event_active && event_phase === 'normal') {
        setAlertLevel('normal');
      } else if (prediction === "Event Detected" && (confidence || 0) >= 0.8) {
        setAlertLevel('critical');
      } else if (prediction === "Event Detected" && (confidence || 0) >= 0.5) {
        setAlertLevel('warning');
      } else if (prediction === "Event Detected" && (confidence || 0) >= 0.3) {
        setAlertLevel('caution');
      } else {
        setAlertLevel('normal');
      }
    }
  }, [data]);

  const alertStyles = {
    critical: 'bg-red-600 text-white',
    warning: 'bg-orange-500 text-white',
    caution: 'bg-yellow-400 text-black',
    normal: 'bg-green-500 text-white'
  };

  const alertMessages = {
    critical: 'Critical risk of rockfall detected!',
    warning: 'High risk of rockfall detected!',
    caution: 'Moderate risk of rockfall detected.',
    normal: 'No significant rockfall risk detected.'
  };

  const getMessage = () => {
    if (eventActive) {
      if (eventPhase === 'normal') return 'Normal readings - All systems operational';
      if (eventPhase === 'warning') return 'WARNING: Receiving unusual readings - Potential event detected!';
      if (eventPhase === 'danger') return 'DANGER: Evacuate immediately - Event imminent!';
      if (eventPhase === 'main_event') return 'EMERGENCY: Event in progress - Take cover!';
    } 
    return alertMessages[alertLevel as keyof typeof alertMessages];
  };

  return (
    <div className={`p-4 rounded-lg shadow mb-4 ${alertStyles[alertLevel as keyof typeof alertStyles]}`}>
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold">TRINETRA Alert Status</h2>
        <div className="flex items-center">
          <div className={`h-3 w-3 rounded-full mr-2 ${isConnected ? 'bg-green-300' : 'bg-red-300'}`} 
               title={isConnected ? 'Connected' : 'Disconnected'}></div>
          <span className="text-sm">{isConnected ? 'Live' : 'Disconnected'}</span>
        </div>
      </div>

      <div className="mt-4">
        <div className="text-2xl font-bold">{getMessage()}</div>
        <div className="mt-2 flex justify-between items-center">
          <div>
            <span className="font-semibold">Risk Level: </span>
            <span className="capitalize">{alertLevel}</span>
            {eventActive && (
              <span className="ml-2 px-2 py-1 bg-red-800 text-white text-xs rounded-full animate-pulse">
                {eventPhase === 'normal' ? 'NORMAL' :
                 eventPhase === 'warning' ? 'WARNING' : 
                 eventPhase === 'danger' ? 'DANGER' : 'EMERGENCY'}
              </span>
            )}
          </div>
          <div className="text-sm">
            <span>Confidence: {(prediction * 100).toFixed(1)}%</span>
            {lastUpdate && <span className="ml-2">Last update: {lastUpdate}</span>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertPanel;
