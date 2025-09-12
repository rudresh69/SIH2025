import React, { useState, useEffect, useMemo } from 'react';

interface ImageModelProps {
  triggerAlert?: boolean;
}

const ImageModel: React.FC<ImageModelProps> = ({ triggerAlert = false }) => {
  const [status, setStatus] = useState<'safe' | 'warning' | 'danger'>('safe');
  const [imageIndex, setImageIndex] = useState(0);
  
  // Mock images for demonstration
  const images = useMemo(() => [
    { url: 'https://via.placeholder.com/400x300/e0f7fa/000000?text=Safe+Rock+Formation', status: 'safe' },
    { url: 'https://via.placeholder.com/400x300/fff9c4/000000?text=Possible+Crack+Detected', status: 'warning' },
    { url: 'https://via.placeholder.com/400x300/ffebee/000000?text=Rockfall+Detected', status: 'danger' }
  ], []);

  useEffect(() => {
    // Cycle through images every 5 seconds for demo purposes
    const interval = setInterval(() => {
      if (!triggerAlert) {
        const nextIndex = (imageIndex + 1) % 2; // Only cycle between safe and warning in normal mode
        setImageIndex(nextIndex);
        setStatus(images[nextIndex].status as 'safe' | 'warning' | 'danger');
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [imageIndex, triggerAlert, images]);

  useEffect(() => {
    // When alert is triggered, show the danger image
    if (triggerAlert) {
      setImageIndex(2); // Index of danger image
      setStatus('danger');
    }
  }, [triggerAlert]);

  const getStatusDisplay = () => {
    switch (status) {
      case 'safe':
        return <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full">Safe ✅</span>;
      case 'warning':
        return <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full">Possible Crack ⚠️</span>;
      case 'danger':
        return <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full">Rockfall 🔴</span>;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow h-full">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Image Model</h3>
        {getStatusDisplay()}
      </div>
      
      <div className="relative">
        <img 
          src={images[imageIndex].url} 
          alt="Rock formation" 
          className="w-full h-64 object-cover rounded-md"
        />
        <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white p-2 text-sm">
          Camera Feed - Under Development
        </div>
      </div>
    </div>
  );
};

export default ImageModel;