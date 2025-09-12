// frontend/src/App.tsx
import React, { useState } from "react";
import "./App.css";

// Import components
import Header from "./components/Header";
import SensorGraphs from "./components/SensorGraphs";
import WeatherForecast from "./components/WeatherForecast";
import AlertPanel from "./components/AlertPanel";
import ImageModel from "./components/ImageModel";
import ModelPredictions from "./components/ModelPredictions";
import RiskIndicator from "./components/RiskIndicator";
import EventLog from "./components/EventLog";
import Footer from "./components/Footer";
import AlertButton from "./components/AlertButton";
// --- REMOVED: BlogSection import is gone ---

function App() {
  const [alertActive, setAlertActive] = useState(false);

  // --- THIS IS THE UPDATED FUNCTION ---
  const handleTriggerAlert = async (eventType: string) => {
    // Prevent triggering a new event if one is already active
    if (alertActive) return;

    console.log(`Triggering ${eventType} event...`);
    setAlertActive(true);

    try {
      // Send the request to your backend to start the simulation
      const response = await fetch(`http://127.0.0.1:8000/api/trigger_event/${eventType}`, {
        method: 'POST',
      });

      if (!response.ok) {
        console.error('Failed to trigger event on the backend.');
      } else {
        const result = await response.json();
        console.log('Backend response:', result.message);
      }
    } catch (error) {
      console.error('Error sending trigger request:', error);
    }

    // The frontend alert state will reset after 65 seconds
    // (slightly longer than the 60s backend event)
    setTimeout(() => {
      console.log("Resetting frontend alert state.");
      setAlertActive(false);
    }, 65000); // 65 seconds
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <Header />

      <main className="flex-grow p-4">
        <AlertPanel />

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-4">
          <div className="lg:col-span-3">
            <SensorGraphs />
          </div>
          <div className="lg:col-span-1">
            <WeatherForecast />
          </div>
        </div>
        
        <ModelPredictions triggerAlert={alertActive} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
          <ImageModel triggerAlert={alertActive} />
          <RiskIndicator triggerAlert={alertActive} />
        </div>
        
        <div className="mt-4">
            <EventLog triggerAlert={alertActive} />
        </div>
      </main>

      {/* This now correctly passes the new function to your AlertButton */}
      <AlertButton onTriggerAlert={handleTriggerAlert} isAlertActive={alertActive} />
      
      {/* --- REMOVED: BlogSection component is gone --- */}
      <Footer />
    </div>
  );
}

export default App; 