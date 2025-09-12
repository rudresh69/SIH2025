import React, { useState } from 'react';

interface AlertButtonProps {
  // The function now accepts the event type as a string
  onTriggerAlert: (eventType: string) => void;
  isAlertActive: boolean;
}

const eventTypes = [
  { name: 'Rockfall', type: 'rockfall', icon: '🪨' },
  { name: 'Rainfall', type: 'rainfall', icon: '🌧️' },
  { name: 'Landslide', type: 'landslide', icon: '⛰️' },
];

const AlertButton: React.FC<AlertButtonProps> = ({ onTriggerAlert, isAlertActive }) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleTrigger = (eventType: string) => {
    onTriggerAlert(eventType);
    setIsOpen(false);
  };

  return (
    <div className="fixed bottom-20 right-6 z-10">
      {/* Container for the fly-out buttons */}
      <div className="flex flex-col items-center space-y-3">
        {/* The individual event buttons, shown when isOpen is true */}
        {isOpen && !isAlertActive && (
          <div className="flex flex-col items-center space-y-3 bg-white p-3 rounded-xl shadow-lg">
            {eventTypes.map((event) => (
              <button
                key={event.type}
                onClick={() => handleTrigger(event.type)}
                className="w-full px-4 py-2 rounded-lg text-left font-semibold text-gray-700 hover:bg-gray-100 transition-colors flex items-center"
              >
                <span className="mr-3 text-xl">{event.icon}</span>
                <span>{event.name}</span>
              </button>
            ))}
          </div>
        )}

        {/* Main persistent button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          disabled={isAlertActive}
          className={`
            px-6 py-3 rounded-full shadow-lg font-bold text-white
            ${isAlertActive ? 'bg-gray-500 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700'}
            transition-all duration-300 flex items-center transform hover:scale-105
          `}
        >
          <span className="mr-2 text-2xl">🚨</span>
          <span>{isAlertActive ? 'Event Active' : 'Trigger Event'}</span>
        </button>
      </div>
    </div>
  );
};

export default AlertButton;