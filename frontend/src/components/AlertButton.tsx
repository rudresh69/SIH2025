import React from 'react';

interface AlertButtonProps {
  onTriggerAlert: () => void;
  isAlertActive: boolean;
}

const AlertButton: React.FC<AlertButtonProps> = ({ onTriggerAlert, isAlertActive }) => {
  return (
    <div className="fixed bottom-20 right-6 z-10">
      <button
        onClick={onTriggerAlert}
        disabled={isAlertActive}
        className={`
          px-6 py-3 rounded-full shadow-lg font-bold text-white
          ${isAlertActive ? 'bg-gray-500 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700'}
          transition-colors duration-200 flex items-center
        `}
      >
        <span className="mr-2">🚨</span>
        {isAlertActive ? 'Alert Active' : 'Simulate Rockfall Alert'}
      </button>
    </div>
  );
};

export default AlertButton;