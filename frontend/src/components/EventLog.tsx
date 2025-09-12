import React, { useState, useEffect } from 'react';

interface EventLogProps {
  triggerAlert?: boolean;
}

interface LogEntry {
  timestamp: string;
  message: string;
  level: 'info' | 'warning' | 'danger';
}

const EventLog: React.FC<EventLogProps> = ({ triggerAlert = false }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Generate timestamp in format [HH:MM:SS]
  const getTimestamp = () => {
    const now = new Date();
    return `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}]`;
  };

  // Add a new log entry
  const addLogEntry = (message: string, level: 'info' | 'warning' | 'danger') => {
    setLogs(prev => [{ timestamp: getTimestamp(), message, level }, ...prev].slice(0, 100));
  };

  useEffect(() => {
    // Initial log entry
    addLogEntry('System initialized', 'info');
    
    // Add periodic log entries for demonstration
    const interval = setInterval(() => {
      if (!triggerAlert) {
        const randomEntries = [
          { message: 'Sensors stable', level: 'info' as const },
          { message: 'Weather conditions normal', level: 'info' as const },
          { message: 'Image analysis completed', level: 'info' as const },
          { message: 'Minor vibration detected', level: 'info' as const },
          { message: 'Slight increase in humidity', level: 'info' as const }
        ];
        
        const randomEntry = randomEntries[Math.floor(Math.random() * randomEntries.length)];
        addLogEntry(`${randomEntry.message} – SAFE`, randomEntry.level);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (triggerAlert) {
      // Add alert log entries
      addLogEntry('Significant vibration detected – WARNING', 'warning');
      
      setTimeout(() => {
        addLogEntry('Sensor values exceeding thresholds – WARNING', 'warning');
      }, 1000);
      
      setTimeout(() => {
        addLogEntry('Weather risk increased – WARNING', 'warning');
      }, 2000);
      
      setTimeout(() => {
        addLogEntry('Rockfall detected by CNN & Image Model – DANGER', 'danger');
      }, 3000);
    }
  }, [triggerAlert]);

  const getLogEntryClass = (level: string) => {
    switch (level) {
      case 'info':
        return 'text-blue-600';
      case 'warning':
        return 'text-orange-600';
      case 'danger':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow h-full">
      <h3 className="text-lg font-semibold mb-4">Event Log</h3>
      
      <div className="h-64 overflow-y-auto border border-gray-200 rounded p-2 bg-gray-50">
        {logs.map((log, index) => (
          <div key={index} className={`mb-1 ${getLogEntryClass(log.level)}`}>
            <span className="font-mono">{log.timestamp}</span> {log.message}
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