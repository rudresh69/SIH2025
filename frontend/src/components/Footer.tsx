import React from 'react';

const Footer: React.FC = () => {
  return (
    <div className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        
        {/* Main content grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Column 1: About Section */}
          <div className="md:col-span-1">
            <h3 className="text-lg font-semibold text-white mb-4">Rockfall Monitoring</h3>
            <p className="text-sm">
              An advanced AI-powered system for predicting and preventing rockfall hazards, combining sensor data, weather, and image analysis.
            </p>
          </div>

          {/* Column 2: Features/Links */}
          <div>
            <h3 className="text-base font-semibold text-white tracking-wider uppercase mb-4">Features</h3>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="hover:text-white transition-colors">Real-time Monitoring</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Predictive Analytics</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Weather Risk AI</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Early Warning System</a></li>
            </ul>
          </div>

        </div>

        {/* Bottom bar with copyright and social links */}
        <hr className="my-6 border-gray-700" />
        <div className="flex flex-col sm:flex-row justify-between items-center text-sm">
          <p className="text-gray-400">
            &copy; {new Date().getFullYear()} Smart India Hackathon. All Rights Reserved.
          </p>
          <div className="flex space-x-6 mt-4 sm:mt-0">
            <a href="#" className="text-gray-400 hover:text-white transition-colors">Twitter</a>
            <a href="#" className="text-gray-400 hover:text-white transition-colors">GitHub</a>
            <a href="#" className="text-gray-400 hover:text-white transition-colors">LinkedIn</a>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Footer;