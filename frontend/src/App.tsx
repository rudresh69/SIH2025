// frontend/src/App.tsx
import React, { useState } from "react";
import "./App.css";

// Import components
import Header from "./components/Header";
import SensorGraphs from "./components/SensorGraphs";
import WeatherForecast from "./components/WeatherForecast";
import AlertPanel from "./components/AlertPanel";
import ImageModel from "./components/ImageModel";
import RiskIndicator from "./components/RiskIndicator";
import EventLog from "./components/EventLog";
import Footer from "./components/Footer";
import AlertButton from "./components/AlertButton";

function App() {
  const [alertActive, setAlertActive] = useState(false);

  const handleTriggerAlert = async (eventType: string) => {
    if (alertActive) return;
    console.log(`Triggering ${eventType} event...`);
    setAlertActive(true);

    try {
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

    setTimeout(() => {
      console.log("Resetting frontend alert state.");
      setAlertActive(false);
    }, 65000);
  };

  return (
    <div className="flex h-screen bg-gray-200 font-sans">
      
      {/* --- Sidebar (Left Panel for Status) --- */}
      <aside className="w-96 flex-shrink-0 bg-gray-800 text-white p-4 flex flex-col gap-4 overflow-y-auto">
        <Header />
        <AlertPanel />
        {/* --- FIXED: Removed unnecessary triggerAlert prop --- */}
        <RiskIndicator />
        <EventLog />
      </aside>

      {/* --- Main Content (Right, Scrollable Panel for Data) --- */}
      <main className="flex-1 p-6 overflow-y-auto">
        <div className="flex flex-col gap-6">
          <SensorGraphs />
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* --- FIXED: Removed unnecessary triggerAlert prop --- */}
            <ImageModel />
            <WeatherForecast />
          </div>

          <Footer />
        </div>
      </main>

      {/* The Alert Button remains in a fixed position over everything */}
      <AlertButton onTriggerAlert={handleTriggerAlert} isAlertActive={alertActive} />

    </div>
  );
}

export default App;