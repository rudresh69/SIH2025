// frontend/src/components/ImageModel.tsx
import React from "react";
// Removed useWebSocket hook as we won't be using live data for now

interface ImageModelProps {
  // triggerAlert prop is no longer strictly necessary for "under development" but can remain if you want to reuse it later
  triggerAlert?: boolean;
}

const ImageModel: React.FC<ImageModelProps> = () => { // Removed triggerAlert from destructuring as it's not used
  // No need for state or effects to manage status/images if it's "under development"

  const getStatusDisplay = () => {
    return (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
        ⚪ Under Development
      </span> 
    );
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow h-full">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Image Model</h3>
        {getStatusDisplay()}
      </div>

      <div className="relative">
        {/* Placeholder image for under development */}
        <img
          src="/images/placeholder-dev.jpg" // You might need to create a placeholder image, e.g., in public/images
          alt="Image Model Under Development"
          className="w-full h-64 object-cover rounded-md bg-gray-200 flex items-center justify-center text-gray-500"
        />
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-60 text-white text-xl font-bold rounded-md">
          Image Model Under Development
        </div>
        <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white p-2 text-sm text-center">
          Live Feed (Currently Offline)
        </div>
      </div>
    </div>
  );
};

export default ImageModel;