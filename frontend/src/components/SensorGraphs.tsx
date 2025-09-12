import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Mock data for demonstration
const generateMockData = (length: number, type: string) => {
  return Array.from({ length }, (_, i) => ({
    time: `${i}s`,
    value: Math.random() * 100 + (type === 'seismic' ? 50 : type === 'displacement' ? 30 : 20)
  }));
};

const seismicData = generateMockData(20, 'seismic');
const displacementData = generateMockData(20, 'displacement');
const hydroData = generateMockData(20, 'hydro');
const environmentalData = generateMockData(20, 'environmental');

const SensorGraphs: React.FC = () => {
  return (
    <div className="grid grid-cols-2 gap-4 p-4">
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-2">Seismic Sensors</h3>
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={seismicData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#8884d8" activeDot={{ r: 8 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-2">Displacement Sensors</h3>
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={displacementData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#82ca9d" activeDot={{ r: 8 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-2">Hydro Sensors</h3>
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={hydroData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#ffc658" activeDot={{ r: 8 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-2">Environmental Sensors</h3>
        <ResponsiveContainer width="100%" height={150}>
          <LineChart data={environmentalData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#ff7300" activeDot={{ r: 8 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default SensorGraphs;