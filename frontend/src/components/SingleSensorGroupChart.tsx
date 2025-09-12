// src/components/SingleSensorGroupChart.tsx
import React, { useEffect, useRef } from 'react';
// @ts-ignore
import * as Plotly from 'plotly.js-dist';

interface SingleSensorGroupChartProps {
  title: string;
  config: {
    sensors: string[];
    colors: string[];
  };
  timeData: number[];
  sensorData: { [key: string]: number[] };
  labelData?: number[]; // Optional for the "EVENT ACTIVE" line
}

const SingleSensorGroupChart: React.FC<SingleSensorGroupChartProps> = ({ title, config, timeData, sensorData, labelData }) => {
  const plotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!plotRef.current || timeData.length === 0) return;

    const traces: any[] = [];

    // Create a trace for each sensor in this group
    config.sensors.forEach((sensor, index) => {
      traces.push({
        x: timeData,
        y: sensorData[sensor] || [],
        type: 'scatter',
        mode: 'lines',
        name: sensor.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        line: { color: config.colors[index], width: 2 },
        hovertemplate: `<b>%{fullData.name}</b><br>Value: %{y:.3f}<extra></extra>`
      });
    });

    // If labelData is provided (for the "EVENT ACTIVE" line), add its trace
    if (labelData) {
      traces.push({
        x: timeData,
        y: labelData.map(val => (isNaN(val) ? null : val)), // Use nulls to create gaps
        type: 'scatter',
        mode: 'lines',
        name: 'EVENT ACTIVE',
        line: { color: '#ef4444', width: 4, dash: 'dash' },
        hovertemplate: '<b>EVENT ACTIVE</b><extra></extra>'
      });
    }

    const layout = {
      title: { text: title, font: { size: 18, color: '#1f2937' }, x: 0.5, xanchor: 'center' },
      showlegend: true,
      legend: { orientation: 'h', x: 0.5, xanchor: 'center', y: -0.3 },
      margin: { t: 50, b: 80, l: 60, r: 30 },
      paper_bgcolor: '#ffffff',
      plot_bgcolor: '#f9fafb',
      xaxis: { title: 'Time Steps', gridcolor: '#e5e7eb' },
      yaxis: { title: 'Sensor Reading', gridcolor: '#e5e7eb', zeroline: true }
    };

    const plotConfig = { responsive: true, displayModeBar: false, staticPlot: false };

    // Use Plotly.react for efficient updates
    Plotly.react(plotRef.current, traces, layout, plotConfig);

  }, [timeData, sensorData, labelData, title, config]);

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-4">
      <div ref={plotRef} style={{ width: '100%', height: '350px' }} />
    </div>
  );
};

export default SingleSensorGroupChart;