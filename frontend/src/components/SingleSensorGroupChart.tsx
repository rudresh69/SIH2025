import React, { useEffect, useRef } from 'react';
// @ts-ignore
import * as Plotly from 'plotly.js-dist';

interface SingleSensorGroupChartProps {
  title: string;
  config: { sensors: string[]; colors: string[]; };
  timeData: number[];
  sensorData: { [key: string]: number[] };
  labelData?: number[];
}

const SingleSensorGroupChart: React.FC<SingleSensorGroupChartProps> = ({ title, config, timeData, sensorData, labelData }) => {
  const plotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!plotRef.current || timeData.length === 0) return;

    let maxVal = -Infinity;
    let minVal = Infinity;
    config.sensors.forEach(sensor => {
      const series = sensorData[sensor] || [];
      if (series.length > 0) {
        const maxInSeries = Math.max(...series);
        const minInSeries = Math.min(...series);
        if (maxInSeries > maxVal) maxVal = maxInSeries;
        if (minInSeries < minVal) minVal = minInSeries;
      }
    });

    const range = maxVal - minVal;
    const eventLinePosition = maxVal + (range * 0.1) + 0.5;

    const traces: any[] = [];
    config.sensors.forEach((sensor, index) => {
      traces.push({
        x: timeData, y: sensorData[sensor] || [], type: 'scatter', mode: 'lines',
        name: sensor.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
        line: { color: config.colors[index], width: 2 },
        hovertemplate: `<b>%{fullData.name}</b><br>Value: %{y:.3f}<extra></extra>`
      });
    });

    if (labelData) {
      traces.push({
        x: timeData,
        y: labelData.map(signal => (signal === 1 ? eventLinePosition : null)),
        type: 'scatter', mode: 'lines', name: 'EVENT ACTIVE',
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
      xaxis: {
        title: 'Time Steps',
        gridcolor: '#e5e7eb',
        range: [timeData[0], timeData[timeData.length - 1]]
      },
      // --- CHANGED: Y-axis is now always flexible ---
      yaxis: {
        title: 'Sensor Reading',
        gridcolor: '#e5e7eb',
        zeroline: true,
        autorange: true // This makes the axis flexible for all charts
      }
    };

    const plotConfig = { responsive: true, displayModeBar: false, staticPlot: false };
    Plotly.react(plotRef.current, traces, layout, plotConfig);

  }, [timeData, sensorData, labelData, title, config]);

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-4">
      <div ref={plotRef} style={{ width: '100%', height: '350px' }} />
    </div>
  );
};

export default SingleSensorGroupChart;