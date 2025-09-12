import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

type WsMsg = {
  timestamp?: string;
  weather_forecast?: any; // can be array of arrays or array of objects
};

type ForecastPoint = {
  time: string;
  temperature: number;
  humidity: number;
  rainfall: number;
};

const WeatherForecast: React.FC = () => {
  const { data, isConnected } = useWebSocket<WsMsg>();
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);

  useEffect(() => {
    if (!data?.weather_forecast) return;

    const raw = data.weather_forecast;

    // raw may be: [ [rain, temp, hum], ... ] OR [ {rain_sensor_mmhr, temperature_celsius, humidity_percent}, ... ]
    const parsed: ForecastPoint[] = [];
    for (let i = 0; i < raw.length; i++) {
      const step = raw[i];
      if (Array.isArray(step) && step.length >= 3) {
        parsed.push({
          time: `+${i + 1}`,
          rainfall: Number(step[0]),
          temperature: Number(step[1]),
          humidity: Number(step[2])
        });
      } else if (typeof step === 'object' && step !== null) {
        parsed.push({
          time: `+${i + 1}`,
          rainfall: Number(step.rain_sensor_mmhr ?? step[0] ?? 0),
          temperature: Number(step.temperature_celsius ?? step[1] ?? 0),
          humidity: Number(step.humidity_percent ?? step[2] ?? 0)
        });
      }
    }

    setForecast(parsed);
  }, [data]);

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Weather Forecast</h2>
        <div className={`h-3 w-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
      </div>

      {forecast.length > 0 ? (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={forecast}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="temperature" name="Temperature (°C)" dot={false} />
            <Line yAxisId="left" type="monotone" dataKey="humidity" name="Humidity (%)" dot={false} />
            <Line yAxisId="right" type="monotone" dataKey="rainfall" name="Rainfall (mm/hr)" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <div className="flex justify-center items-center h-64">
          <p className="text-gray-500">Waiting for forecast data...</p>
        </div>
      )}
    </div>
  );
};

export default WeatherForecast;
