import React, { useEffect, useState } from 'react';
import { ResponsiveContainer, ComposedChart, Area, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine } from 'recharts';

type ForecastPoint = {
  time: string;
  temperature: number;
  humidity: number;
  rainfall: number;
};

type OpenMeteoResponse = {
  hourly: {
    time: string[];
    temperature_2m: number[];
    relativehumidity_2m: number[];
    precipitation: number[];
  }
};

const WeatherForecast: React.FC = () => {
  const [forecast, setForecast] = useState<ForecastPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const fetchWeatherData = async () => {
      setLoading(true);
      setError(null);
      
      const lat = 18.52; // Pune Latitude
      const lon = 73.86; // Pune Longitude
      
      // --- CHANGED: Added `&timezone=auto` to the URL ---
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&hourly=temperature_2m,relativehumidity_2m,precipitation&forecast_days=1&timezone=auto`;

      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error('Failed to fetch data from weather API.');
        }
        const apiData: OpenMeteoResponse = await response.json();

        const parsed: ForecastPoint[] = [];
        const now = new Date();
        for (let i = 0; i < apiData.hourly.time.length; i++) {
            const forecastTime = new Date(apiData.hourly.time[i]);
            if (forecastTime > now && parsed.length < 12) {
                parsed.push({
                    time: forecastTime.toLocaleTimeString([], { hour: 'numeric', hour12: true }),
                    temperature: apiData.hourly.temperature_2m[i],
                    humidity: apiData.hourly.relativehumidity_2m[i],
                    rainfall: apiData.hourly.precipitation[i],
                });
            }
        }
        setForecast(parsed);
      } catch (err) {
        setError("Could not load weather forecast.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchWeatherData();
  }, []); 

  const currentForecast = forecast.length > 0 ? forecast[0] : null;

  const getWeatherCondition = (rainfall: number): string => {
    if (rainfall > 5) return 'Heavy Rain';
    if (rainfall > 0.5) return 'Light Rain';
    return 'Clear';
  };
  
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white/80 backdrop-blur-sm p-3 rounded-lg shadow-lg border border-gray-200">
          <p className="font-bold text-gray-700">{`Time: ${label}`}</p>
          {payload.map((pld: any) => ( <p key={pld.dataKey} style={{ color: pld.color }}>{`${pld.name}: ${pld.value.toFixed(1)}`}</p> ))}
        </div>
      );
    }
    return null;
  };

  const renderContent = () => {
    if (loading) {
      return <div className="flex-grow flex justify-center items-center"><p className="text-gray-500">Loading live weather for Pune...</p></div>;
    }
    if (error) {
      return <div className="flex-grow flex justify-center items-center"><p className="text-red-500">{error}</p></div>;
    }
    if (!currentForecast) {
        return <div className="flex-grow flex justify-center items-center"><p className="text-gray-500">No forecast data available.</p></div>
    }
    return (
        <>
            <div className="flex items-center justify-between text-center border-b pb-4 mb-4 px-2">
                <div className="w-1/3 text-left">
                    <div className="text-lg font-bold text-gray-800">{getWeatherCondition(currentForecast.rainfall)}</div>
                    <div className="text-sm text-gray-500">Condition</div>
                </div>
                <div className="w-1/3">
                    <div className="text-4xl font-bold text-gray-800">{currentForecast.temperature.toFixed(1)}°C</div>
                    <div className="text-sm text-gray-500">Upcoming Hour</div>
                </div>
                <div className="w-1/3 text-right text-sm space-y-1 text-gray-600">
                    <p>Hum: <strong>{currentForecast.humidity.toFixed(1)}%</strong></p>
                    <p>Rain: <strong>{currentForecast.rainfall.toFixed(1)} mm/hr</strong></p>
                </div>
            </div>
            <div className="flex-grow">
                <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={forecast} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#f97316" stopOpacity={0.7}/><stop offset="95%" stopColor="#f97316" stopOpacity={0}/></linearGradient>
                            <linearGradient id="colorHum" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10b981" stopOpacity={0.7}/><stop offset="95%" stopColor="#10b981" stopOpacity={0}/></linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                        <XAxis dataKey="time" fontSize={10} tickLine={false} axisLine={false} />
                        <YAxis yAxisId="left" fontSize={12} tickLine={false} axisLine={false} domain={['dataMin - 5', 'dataMax + 5']} />
                        <YAxis yAxisId="right" orientation="right" fontSize={12} tickLine={false} axisLine={false} domain={[0, 'dataMax + 2']} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend iconSize={10} wrapperStyle={{fontSize: "12px"}} />
                        <Area yAxisId="left" type="monotone" dataKey="temperature" name="Temp (°C)" stroke="#f97316" fill="url(#colorTemp)" />
                        <Area yAxisId="left" type="monotone" dataKey="humidity" name="Humidity (%)" stroke="#10b981" fill="url(#colorHum)" />
                        <Bar yAxisId="right" dataKey="rainfall" name="Rain (mm/hr)" fill="#3b82f6" barSize={20} />
                        <ReferenceLine y={5} yAxisId="right" label={{ value: 'Heavy Rain', position: 'insideTopRight', fill: '#dc2626', fontSize: 10 }} stroke="#dc2626" strokeDasharray="3 3" />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>
        </>
    );
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow h-full flex flex-col">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-xl font-bold text-gray-800">Live Weather</h2>
      </div>
      <p className="text-xs text-gray-400 mb-4">Pune, India · {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
      {renderContent()}
    </div>
  );
};

export default WeatherForecast;