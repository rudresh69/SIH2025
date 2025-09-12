import React from 'react';

interface WeatherData {
  rainfall: number;
  humidity: number;
  windSpeed: number;
  temperature: number;
  riskLevel: 'low' | 'medium' | 'high';
}

// Mock data for demonstration
const mockWeatherData: WeatherData = {
  rainfall: 2.5,
  humidity: 65,
  windSpeed: 12,
  temperature: 28,
  riskLevel: 'medium'
};

const WeatherWidget: React.FC = () => {
  const { rainfall, humidity, windSpeed, temperature, riskLevel } = mockWeatherData;
  
  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low':
        return 'bg-green-500';
      case 'medium':
        return 'bg-orange-500';
      case 'high':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow h-full">
      <h3 className="text-lg font-semibold mb-4">Weather Conditions</h3>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-blue-50 p-3 rounded-md">
          <div className="flex items-center">
            <span className="text-blue-500 text-2xl mr-2">🌧️</span>
            <div>
              <p className="text-sm text-gray-500">Rainfall</p>
              <p className="font-bold">{rainfall} mm</p>
            </div>
          </div>
        </div>
        
        <div className="bg-blue-50 p-3 rounded-md">
          <div className="flex items-center">
            <span className="text-blue-500 text-2xl mr-2">💧</span>
            <div>
              <p className="text-sm text-gray-500">Humidity</p>
              <p className="font-bold">{humidity}%</p>
            </div>
          </div>
        </div>
        
        <div className="bg-blue-50 p-3 rounded-md">
          <div className="flex items-center">
            <span className="text-blue-500 text-2xl mr-2">🌬️</span>
            <div>
              <p className="text-sm text-gray-500">Wind Speed</p>
              <p className="font-bold">{windSpeed} km/h</p>
            </div>
          </div>
        </div>
        
        <div className="bg-blue-50 p-3 rounded-md">
          <div className="flex items-center">
            <span className="text-blue-500 text-2xl mr-2">🌡️</span>
            <div>
              <p className="text-sm text-gray-500">Temperature</p>
              <p className="font-bold">{temperature}°C</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-4">
        <p className="text-sm font-semibold mb-2">Weather Risk Level:</p>
        <div className="w-full h-6 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className={`h-full ${getRiskColor(riskLevel)} text-xs text-white flex items-center justify-center`}
            style={{ width: riskLevel === 'low' ? '33%' : riskLevel === 'medium' ? '66%' : '100%' }}
          >
            {riskLevel.toUpperCase()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherWidget;