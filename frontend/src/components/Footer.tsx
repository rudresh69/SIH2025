import React from 'react';

const Footer: React.FC = () => {
  return (
    <div className="bg-gray-800 text-white py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2">
            <h3 className="text-lg font-semibold mb-3">Rockfall Monitoring System</h3>
            <p className="text-gray-300 text-sm mb-4">
              An advanced AI-powered system designed to predict and prevent rockfall hazards in mountainous regions.
              Our solution combines sensor data, weather information, and image analysis to provide early warnings.
            </p>
            <p className="text-gray-400 text-xs">
              © 2023 Smart India Hackathon Project. All rights reserved.
            </p>
          </div>
          
          <div className="col-span-1">
            <h3 className="text-lg font-semibold mb-3">Features</h3>
            <ul className="text-gray-300 text-sm space-y-2">
              <li>Real-time sensor monitoring</li>
              <li>Weather risk assessment</li>
              <li>AI image analysis</li>
              <li>Predictive analytics</li>
              <li>Early warning system</li>
            </ul>
          </div>
          
          <div className="col-span-1">
            <h3 className="text-lg font-semibold mb-3">Contact</h3>
            <ul className="text-gray-300 text-sm space-y-2">
              <li>Email: info@rockfallmonitor.in</li>
              <li>Phone: +91 123 456 7890</li>
              <li>Address: IIT Delhi, Hauz Khas</li>
              <li>New Delhi, India - 110016</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Footer;
