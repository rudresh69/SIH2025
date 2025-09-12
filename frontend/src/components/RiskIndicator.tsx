import React from 'react';

interface RiskIndicatorProps {
  triggerAlert?: boolean;
}

type RiskLevel = 'safe' | 'danger';

const RiskIndicator: React.FC<RiskIndicatorProps> = ({ triggerAlert = false }) => {
  const riskLevel: RiskLevel = triggerAlert ? 'danger' : 'safe';

  const getRiskDisplay = () => {
    switch (riskLevel) {
      case 'safe':
        return {
          color: 'bg-green-500',
          text: 'SAFE',
          icon: '🟢'
        };
      case 'warning' as string:
        return {
          color: 'bg-orange-500',
          text: 'WARNING',
          icon: '🟠'
        };
      case 'danger':
        return {
          color: 'bg-red-500',
          text: 'DANGER',
          icon: '🔴'
        };
      default:
        return {
          color: 'bg-gray-500',
          text: 'UNKNOWN',
          icon: '⚪'
        };
    }
  };

  const { color, text, icon } = getRiskDisplay();

  return (
    <div className="bg-white p-4 rounded-lg shadow h-full">
      <h3 className="text-lg font-semibold mb-4">Final Risk Indicator</h3>
      
      <div className={`${color} rounded-lg p-6 text-white text-center`}>
        <div className="text-6xl mb-2">{icon}</div>
        <div className="text-4xl font-bold">{text}</div>
      </div>
    </div>
  );
};

export default RiskIndicator;