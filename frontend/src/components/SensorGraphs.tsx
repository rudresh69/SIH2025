import React, { useEffect, useState, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import Sparkline from './Sparkline'; 
import SingleSensorGroupChart from './SingleSensorGroupChart';

type SensorReadings = {
  timestamp: string;
  accelerometer: number;
  geophone: number;
  seismometer: number;
  crack_sensor: number;
  inclinometer: number;
  extensometer: number;
  moisture_sensor: number;
  piezometer: number;
  rain_sensor_mmhr: number;
  temperature_celsius: number;
  humidity_percent: number;
  label?: number;
  prediction?: string | null;
  confidence?: number;
  weather_forecast?: any;
};

const MAX_PLOT_POINTS = 200;

const SENSOR_GROUPS = {
  "Seismic Sensors": {
    sensors: ["accelerometer", "geophone", "seismometer"],
    colors: ["#1f77b4", "#ff7f0e", "#2ca02c"],
  },
  "Displacement Sensors": {
    sensors: ["crack_sensor", "inclinometer", "extensometer"],
    colors: ["#d62728", "#9467bd", "#8c564b"],
  },
  "Hydrological Sensors": {
    sensors: ["moisture_sensor", "piezometer"],
    colors: ["#e377c2", "#7f7f7f"],
  },
  "Environmental Sensors": {
    sensors: ["rain_sensor_mmhr", "temperature_celsius", "humidity_percent"],
    colors: ["#17becf", "#bcbd22", "#ff9896"],
  }
};

const SensorGraphs: React.FC = () => {
  const { data, isConnected } = useWebSocket<SensorReadings>();
  const [timeData, setTimeData] = useState<number[]>([]);
  const [sensorData, setSensorData] = useState<{[key: string]: number[]}>({});
  const [labelData, setLabelData] = useState<number[]>([]);
  const dataCounter = useRef(0);

  useEffect(() => {
    const initialData: {[key: string]: number[]} = {};
    Object.values(SENSOR_GROUPS).forEach(group => group.sensors.forEach(sensor => { initialData[sensor] = []; }));
    setSensorData(initialData);
  }, []);

  useEffect(() => {
    if (!data) return;
    const isEventActive = (data.label && data.label > 0) || (data.prediction === "Event Detected");
    dataCounter.current += 1;
    setTimeData(prev => [...prev, dataCounter.current].slice(-MAX_PLOT_POINTS));
    setLabelData(prev => [...prev, isEventActive ? 5 : NaN].slice(-MAX_PLOT_POINTS));
    setSensorData(prev => {
      const newData = { ...prev };
      Object.values(SENSOR_GROUPS).forEach(group => {
        group.sensors.forEach(sensor => {
          if (newData[sensor]) {
            newData[sensor] = [...newData[sensor], data[sensor as keyof SensorReadings] || 0].slice(-MAX_PLOT_POINTS);
          }
        });
      });
      return newData;
    });
  }, [data]);

  const currentEvent = data && ((data.label && data.label > 0) || (data.prediction === "Event Detected"));

  return (
    <div className="bg-gradient-to-br from-gray-50 to-blue-50 p-4 lg:p-6 space-y-6">
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(SENSOR_GROUPS).map(([groupName, config]) => (
          <SingleSensorGroupChart
            key={groupName}
            title={groupName}
            config={config}
            timeData={timeData}
            sensorData={sensorData}
            // --- CHANGED: Pass labelData to every chart ---
            labelData={labelData}
          />
        ))}
      </div>

      {/* Status Bar */}
      <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
        <div className="flex flex-wrap justify-between items-center text-sm text-gray-600 gap-2">
          <div className="flex items-center gap-4">
            <span>📊 {timeData.length}/{MAX_PLOT_POINTS}</span>
            <span>|</span>
            <span><div className={`inline-block h-2 w-2 rounded-full mr-1 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />{isConnected ? 'LIVE' : 'OFFLINE'}</span>
          </div>
          <div className="font-mono text-xs">
            {currentEvent ? 'EVENT MODE' : 'NORMAL MODE'}
          </div>
          <div className="flex items-center gap-4">
            {data && (<span>🕐 {new Date().toLocaleTimeString()}</span>)}
          </div>
        </div>
      </div>

      {/* Sensor Groups Info with Sparklines */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {Object.entries(SENSOR_GROUPS).map(([groupName, config]) => {
          const sparklineData = sensorData[config.sensors[0]] || [];
          return (
            <div key={groupName} className="bg-white rounded-lg shadow border border-gray-200 p-4">
              <h3 className="font-semibold text-gray-800 mb-2">{groupName}</h3>
              <Sparkline data={sparklineData} color={config.colors[0]} />
              <div className="space-y-1 mt-2">
                {config.sensors.map((sensor, index) => {
                  const currentValue = data?.[sensor as keyof SensorReadings] ?? 0;
                  return (
                    <div key={sensor} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: config.colors[index] }}
                        />
                        <span className="text-gray-600">
                          {sensor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      </div>
                      <span className={`font-mono text-xs ${
                        currentEvent ? 'text-red-600 font-bold' : 'text-gray-700'
                      }`}>
                        {Number(currentValue).toFixed(3)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SensorGraphs;  