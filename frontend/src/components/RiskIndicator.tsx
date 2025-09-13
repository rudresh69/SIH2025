import React, { useEffect, useState, useRef } from 'react';

// The data structure we expect from the GET /alert endpoint
type AlertStatus = {
  mode: 'safe' | 'warning' | 'emergency';
  location: string;
};

const RiskIndicator: React.FC = () => {
  const [alertStatus, setAlertStatus] = useState<AlertStatus>({ mode: 'safe', location: '' });
  const [error, setError] = useState<string | null>(null);

  // A ref to hold the audio element for the siren
  const audioRef = useRef<HTMLAudioElement>(null);

  // Poll backend every 2 seconds
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/alert');
        if (!response.ok) throw new Error('Could not connect to the alert system.');
        const data: AlertStatus = await response.json();
        setAlertStatus(data);
        setError(null);
      } catch (err) {
        console.error(err);
        setError('Connection to alert system lost.');
      }
    };

    fetchStatus();
    const intervalId = setInterval(fetchStatus, 2000);
    return () => clearInterval(intervalId);
  }, []);

  // Control siren playback
  useEffect(() => {
    if (audioRef.current) {
      if (alertStatus.mode === 'emergency') {
        audioRef.current.play().catch(err => console.log("⚠️ Audio play blocked by browser:", err));
      } else {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
    }
  }, [alertStatus.mode]);

  // UI color & text
  let color = 'bg-green-600';
  let text = 'SAFE';
  if (error) {
    color = 'bg-gray-500';
    text = 'OFFLINE';
  } else if (alertStatus.mode === 'emergency') {
    color = 'bg-red-600 animate-pulse';
    text = 'EMERGENCY';
  } else if (alertStatus.mode === 'warning') {
    color = 'bg-orange-500';
    text = 'WARNING';
  }

  return (
    <div className={`${color} p-4 rounded-lg shadow-lg text-white transition-colors duration-500 flex flex-col justify-center items-center h-64`}>
      <div className="text-5xl font-bold tracking-wider">{text}</div>
      {alertStatus.location && !error && (
        <div className="text-lg mt-2 font-semibold bg-black/20 px-3 py-1 rounded-full">
          {alertStatus.location}
        </div>
      )}
      {error && (
        <div className="text-sm mt-2 font-light">
          {error}
        </div>
      )}

      {/* Local siren sound served from public/audio/ */}
      <audio ref={audioRef} src="/audio/civil-defense-siren-128262.mp3" loop />
    </div>
  );
};

export default RiskIndicator;