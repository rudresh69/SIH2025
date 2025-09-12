import React, { useState } from 'react';
import './App.css';

// Import components
import Header from './components/Header';
import SensorGraphs from './components/SensorGraphs';
import WeatherWidget from './components/WeatherWidget';
import ImageModel from './components/ImageModel';
import ModelPredictions from './components/ModelPredictions';
import RiskIndicator from './components/RiskIndicator';
import EventLog from './components/EventLog';
import Footer from './components/Footer';
import AlertButton from './components/AlertButton';
import BlogSection from './components/BlogSection';

function App() {
  const [alertActive, setAlertActive] = useState(false);

  const handleTriggerAlert = () => {
    setAlertActive(true);
    
    // Reset alert after 30 seconds for demo purposes
    setTimeout(() => {
      setAlertActive(false);
    }, 30000);
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      <Header />
      
      <main className="flex-grow p-4">
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div className="col-span-3">
            <SensorGraphs />
          </div>
          <div className="col-span-1">
            <WeatherWidget />
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="col-span-2">
            <ImageModel triggerAlert={alertActive} />
          </div>
          <div className="col-span-1">
            <div className="bg-white p-4 rounded-lg shadow text-center">
              <p className="text-sm text-gray-500 mb-2">Date & Time Log</p>
              <p className="font-semibold">
                {new Date().toLocaleDateString()} - Updated every 3 hours
              </p>
            </div>
          </div>
        </div>
        
        <ModelPredictions triggerAlert={alertActive} />
        
        <div className="grid grid-cols-5 gap-4 mt-4">
          <div className="col-span-2">
            <RiskIndicator triggerAlert={alertActive} />
          </div>
          <div className="col-span-3">
            <EventLog triggerAlert={alertActive} />
          </div>
        </div>
      </main>
      
      <AlertButton onTriggerAlert={handleTriggerAlert} isAlertActive={alertActive} />
      
      <BlogSection />
      
      <Footer />
    </div>
  );
}

export default App;
