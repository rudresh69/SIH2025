import React from 'react';

const BlogSection: React.FC = () => {
  const blogPosts = [
    {
      id: 1,
      title: 'Understanding Rockfall Risks',
      date: 'June 15, 2023',
      excerpt: 'Rockfalls are a common natural hazard in mountainous regions and can pose significant risks to infrastructure and human safety.',
      imageUrl: '/images/rockfall-monitoring.svg'
    },
    {
      id: 2,
      title: 'AI-Powered Rockfall Detection',
      date: 'July 22, 2023',
      excerpt: 'Modern machine learning algorithms can analyze sensor data and images to predict potential rockfall events before they occur.',
      imageUrl: '/images/rockfall-monitoring.svg'
    },
    {
      id: 3,
      title: 'Implementing Early Warning Systems',
      date: 'August 10, 2023',
      excerpt: 'Early warning systems that combine sensor networks with predictive analytics can save lives by providing timely alerts.',
      imageUrl: '/images/rockfall-monitoring.svg'
    }
  ];

  return (
    <div className="bg-white py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-8 text-gray-800">Latest Updates</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {blogPosts.map(post => (
            <div key={post.id} className="bg-gray-50 rounded-lg overflow-hidden shadow-md transition-transform duration-300 hover:shadow-lg hover:-translate-y-1">
              <img 
                src={post.imageUrl} 
                alt={post.title} 
                className="w-full h-48 object-cover"
              />
              <div className="p-4">
                <p className="text-sm text-gray-500 mb-1">{post.date}</p>
                <h3 className="text-xl font-semibold mb-2 text-gray-800">{post.title}</h3>
                <p className="text-gray-600">{post.excerpt}</p>
                <button className="mt-4 text-blue-600 hover:text-blue-800 font-medium">Read More →</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BlogSection;