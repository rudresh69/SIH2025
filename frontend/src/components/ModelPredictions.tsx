import React from 'react';

interface ModelPredictionsProps {
  triggerAlert?: boolean;
}

type WeatherRiskType = 'Low' | 'Medium' | 'High';
type ImageRiskType = 'Normal' | 'Warning' | 'Rockfall';

const ModelPredictions: React.FC<ModelPredictionsProps> = ({ triggerAlert = false }) => {
  // Mock data for demonstration
  const sensorRisk = triggerAlert ? 85 : 25;
  const weatherRisk: WeatherRiskType = triggerAlert ? 'High' : 'Low';
  const imageRisk: ImageRiskType = triggerAlert ? 'Rockfall' : 'Normal';

  const getSensorRiskColor = (risk: number) => {
    if (risk < 30) return 'text-green-500';
    if (risk < 70) return 'text-orange-500';
    return 'text-red-500';
  };

  const getWeatherRiskColor = (risk: string) => {
    switch (risk) {
      case 'Low':
        return 'text-green-500';
      case 'Medium':
        return 'text-orange-500';
      case 'High':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getImageRiskColor = (risk: string) => {
    switch (risk) {
      case 'Normal':
        return 'text-green-500';
      case 'Warning':
        return 'text-orange-500';
      case 'Rockfall':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="grid grid-cols-3 gap-4 p-4">
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Sensor Risk (1D-CNN)</h3>
        <div className="flex flex-col items-center">
          <div className="w-32 h-32 rounded-full border-8 border-gray-200 flex items-center justify-center mb-4">
            <span className={`text-4xl font-bold ${getSensorRiskColor(sensorRisk)}`}>{sensorRisk}%</span>
          </div>
          <span className={`font-semibold ${getSensorRiskColor(sensorRisk)}`}>
            {sensorRisk < 30 ? 'Normal' : sensorRisk < 70 ? 'Warning' : 'Rockfall'}
          </span>
        </div>
      </div>

      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Weather Risk</h3>
        <div className="flex flex-col items-center">
          <div className="w-32 h-32 rounded-full border-8 border-gray-200 flex items-center justify-center mb-4">
            <span className={`text-4xl font-bold ${getWeatherRiskColor(weatherRisk)}`}>{weatherRisk}</span>
          </div>
          <span className={`font-semibold ${getWeatherRiskColor(weatherRisk)}`}>
            {weatherRisk === 'Low' ? 'Safe Conditions' : 
             (weatherRisk as string) === 'Medium' ? 'Caution Advised' : 
             (weatherRisk as string) === 'High' ? 'Dangerous Conditions' : 
             'Unknown'}
          </span>
        </div>
      </div>

      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Image Risk (Camera Model)</h3>
        <div className="flex flex-col items-center">
          <div className="w-32 h-32 rounded-full border-8 border-gray-200 flex items-center justify-center mb-4">
            <span className={`text-4xl font-bold ${getImageRiskColor(imageRisk)}`}>{imageRisk}</span>
          </div>
          <span className={`font-semibold ${getImageRiskColor(imageRisk)}`}>
            {imageRisk === 'Normal' ? 'No Issues Detected' : 
             (imageRisk as string) === 'Warning' ? 'Possible Issues' : 
             (imageRisk as string) === 'Rockfall' ? 'Critical Issues' : 
             'Unknown'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ModelPredictions;