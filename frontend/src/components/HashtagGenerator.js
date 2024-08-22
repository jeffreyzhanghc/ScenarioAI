import React, { useState } from 'react';
import { Search, Hash } from 'lucide-react';

// Mock function to generate hashtags
const generateHashtags = (keywords) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const hashtags = keywords.split(' ').map(word => `#${word.toLowerCase()}`);
      resolve({
        popular: hashtags.slice(0, 3),
        niche: hashtags.slice(3),
        related: [`#travel`, `#vacation`, `#wanderlust`]
      });
    }, 1000); // Simulate API delay
  });
};

const HashtagGenerator = () => {
  const [keywords, setKeywords] = useState('');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const hashtagResults = await generateHashtags(keywords);
      setResults(hashtagResults);
    } catch (error) {
      console.error('Error generating hashtags:', error);
    }
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 py-4 bg-white">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500">
            Scenario AI
          </div>
          <nav className="hidden md:flex space-x-4">
            <a href="#" className="text-gray-600 hover:text-gray-900">Products</a>
            <a href="#" className="text-gray-600 hover:text-gray-900">Use Cases</a>
            <a href="#" className="text-gray-600 hover:text-gray-900">Resources</a>
            <a href="#" className="text-gray-600 hover:text-gray-900">For Business</a>
            <a href="#" className="text-gray-600 hover:text-gray-900">Pricing</a>
          </nav>
          <div className="flex space-x-4">
            <button className="text-gray-600 hover:text-gray-900">Talk to Sales</button>
            <button className="bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 text-white px-4 py-2 rounded-full hover:opacity-90 transition duration-300">
              Dashboard
            </button>
          </div>
        </div>
      </header>
      <main className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto text-center">
          <div className="inline-block bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 text-white rounded-full px-3 py-1 text-sm font-semibold mb-4">
            Scenario AI
          </div>
          <h1 className="text-5xl font-bold mb-4 text-gray-900">Hashtag Generator</h1>
          <p className="text-xl text-gray-600 mb-8">
            Generate the best hashtags to increase your content's visibility. Use Scenario AI's instant hashtag generator
          </p>
          <form onSubmit={handleSubmit} className="mb-8">
            <label htmlFor="keywords" className="block text-left text-sm font-medium text-gray-700 mb-2">
              Keywords
            </label>
            <div className="relative">
              <input
                type="text"
                id="keywords"
                className="w-full px-4 py-2 border border-gray-300 rounded-full focus:ring-pink-500 focus:border-pink-500"
                placeholder="European Beaches"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                required
              />
            </div>
            <button 
              type="submit"
              className="mt-4 bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 text-white font-bold py-3 px-6 rounded-full transition duration-300 flex items-center justify-center w-full hover:opacity-90"
              disabled={isLoading}
            >
              {isLoading ? 'Generating...' : 'Generate Hashtags'}
              <Search className="ml-2" size={20} />
            </button>
          </form>
          
          {results && (
            <div className="mt-8 bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-bold mb-4 text-gray-900">Generated Hashtags</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">Popular</h3>
                  <div className="flex flex-wrap gap-2">
                    {results.popular.map((tag, index) => (
                      <span key={index} className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-sm">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">Niche</h3>
                  <div className="flex flex-wrap gap-2">
                    {results.niche.map((tag, index) => (
                      <span key={index} className="bg-pink-100 text-pink-800 px-2 py-1 rounded-full text-sm">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">Related</h3>
                  <div className="flex flex-wrap gap-2">
                    {results.related.map((tag, index) => (
                      <span key={index} className="bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-sm">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default HashtagGenerator;
