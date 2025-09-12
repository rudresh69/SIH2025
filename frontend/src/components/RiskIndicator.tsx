import React, { useEffect, useState, useRef } from 'react';

// The data structure we expect from the GET /alert endpoint
type AlertStatus = {
  mode: 'safe' | 'warning' | 'emergency';
  location: string;
};

const RiskIndicator: React.FC = () => {
  // State to hold the status fetched from the API
  const [alertStatus, setAlertStatus] = useState<AlertStatus>({ mode: 'safe', location: '' });
  const [error, setError] = useState<string | null>(null);
  
  // A ref to hold the audio element for the siren
  const audioRef = useRef<HTMLAudioElement>(null);

  // This effect polls the backend for the alert status every 2 seconds
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/alert');
        if (!response.ok) {
          throw new Error('Could not connect to the alert system.');
        }
        const data: AlertStatus = await response.json();
        setAlertStatus(data);
        setError(null);
      } catch (err) {
        console.error(err);
        setError('Connection to alert system lost.');
      }
    };

    fetchStatus(); // Fetch immediately on load
    const intervalId = setInterval(fetchStatus, 2000); // And then poll every 2 seconds

    // Cleanup function to stop polling when the component is removed
    return () => clearInterval(intervalId);
  }, []);

  // This effect controls the siren sound based on the alert status
  useEffect(() => {
    if (audioRef.current) {
      if (alertStatus.mode === 'emergency') {
        // Play audio alert for danger and main event phases
        console.log("🚨 EMERGENCY ALERT - Playing audio alert");
        // Create a simple beep sound using Web Audio API
        try {
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
          const oscillator = audioContext.createOscillator();
          const gainNode = audioContext.createGain();
          
          oscillator.connect(gainNode);
          gainNode.connect(audioContext.destination);
          
          oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
          oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
          oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2);
          
          gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
          gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
          
          oscillator.start(audioContext.currentTime);
          oscillator.stop(audioContext.currentTime + 0.5);
        } catch (e) {
          console.log("🚨 EMERGENCY ALERT - Audio alert (Web Audio API not supported)");
        }
      } else {
        audioRef.current.pause();
        audioRef.current.currentTime = 0; // Rewind the sound
      }
    }
  }, [alertStatus.mode]);

  // Determine color and text based on the fetched mode
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

      {/* Hidden audio element for the siren */}
      <audio ref={audioRef} src="/civil-defense-siren-128262.mp3" loop />
    </div>
  );
};

export default RiskIndicator;