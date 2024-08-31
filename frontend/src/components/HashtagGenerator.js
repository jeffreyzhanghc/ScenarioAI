import React, { useState, useMemo } from 'react';
import { Search, Hash } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const API_BASE_URL = 'http://127.0.0.1:5000';

const HashtagGenerator = () => {
  const [keywords, setKeywords] = useState('');
  const [inputHashtags, setInputHashtags] = useState('');
  const [results, setResults] = useState(null);
  const [topHashtags, setTopHashtags] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const chartColors = ['#9333EA', '#EC4899', '#F97316', '#8B5CF6', '#DB2777'];

  const topHashtagsData = useMemo(() => {
    return topHashtags
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }, [topHashtags]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          keyword: keywords,
          hashtags: inputHashtags.split(' ').filter(tag => tag.startsWith('#'))
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate hashtags and scenarios');
      }

      const data = await response.json();
      setTopHashtags(data.top_hashtags);
      setScenarios(data.scenarios);
      
      // Process hashtags for display
      const allHashtags = data.scenarios.flatMap(scenario => scenario.hashtags);
      setResults({
        popular: allHashtags.slice(0, 5),
        niche: allHashtags.slice(5, 10),
        related: allHashtags.slice(10, 15)
      });

    } catch (error) {
      console.error('Error:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 py-4 bg-white">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <div className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500">
            Scenario AI
          </div>
          <nav className="hidden md:flex space-x-4">
            <a href="https://github.com/jeffreyzhanghc/ScenarioAI/tree/main/frontend" className="text-gray-600 hover:text-gray-900">Products</a>
            <a href="https://github.com/jeffreyzhanghc/ScenarioAI/tree/main/frontend" className="text-gray-600 hover:text-gray-900">Use Cases</a>
            <a href="https://github.com/jeffreyzhanghc/ScenarioAI/tree/main/frontend" className="text-gray-600 hover:text-gray-900">Resources</a>
            <a href="https://github.com/jeffreyzhanghc/ScenarioAI/tree/main/frontend" className="text-gray-600 hover:text-gray-900">For Business</a>
            <a href="https://github.com/jeffreyzhanghc/ScenarioAI/tree/main/frontend" className="text-gray-600 hover:text-gray-900">Pricing</a>
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
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 text-white rounded-full px-3 py-1 text-sm font-semibold mb-4">
            Scenario AI
          </div>
          <h1 className="text-5xl font-bold mb-4 text-gray-900">Hashtag Generator</h1>
          <p className="text-xl text-gray-600 mb-8">
            Generate the best hashtags and content scenarios to increase your content's visibility. Use Scenario AI's instant generator
          </p>
          <form onSubmit={handleSubmit} className="mb-8">
            <div className="mb-4">
              <label htmlFor="keywords" className="block text-left text-sm font-medium text-gray-700 mb-2">
                Keywords
              </label>
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
            <div className="mb-4">
              <label htmlFor="inputHashtags" className="block text-left text-sm font-medium text-gray-700 mb-2">
                Input Hashtags
              </label>
              <input
                type="text"
                id="inputHashtags"
                className="w-full px-4 py-2 border border-gray-300 rounded-full focus:ring-pink-500 focus:border-pink-500"
                placeholder="#travel #adventure"
                value={inputHashtags}
                onChange={(e) => setInputHashtags(e.target.value)}
              />
            </div>
            <button 
              type="submit"
              className="mt-4 bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 text-white font-bold py-3 px-6 rounded-full transition duration-300 flex items-center justify-center w-full hover:opacity-90"
              disabled={isLoading}
            >
              {isLoading ? 'Generating...' : 'Generate Hashtags and Scenarios'}
              <Search className="ml-2" size={20} />
            </button>
          </form>
          
          {error && (
            <div className="mt-4 p-4 bg-red-100 text-red-700 rounded-lg">
              Error: {error}
            </div>
          )}

        {topHashtagsData.length > 0 && (
                <div className="mt-8 bg-white p-6 rounded-lg shadow-lg">
                  <h2 className="text-2xl font-bold mb-4 text-gray-900">Top 10 Hashtags</h2>
                  <div className="h-96">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={topHashtagsData}
                        layout="vertical"
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <XAxis type="number" />
                        <YAxis dataKey="name" type="category" width={150} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: 'rgba(255, 255, 255, 0.8)',
                            border: 'none',
                            borderRadius: '4px',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                          }}
                          cursor={{ fill: 'rgba(0, 0, 0, 0.1)' }}
                        />
                        <Bar dataKey="count" barSize={20}>
                          {topHashtagsData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}



          {scenarios.length > 0 && (
            <div className="mt-8 bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-bold mb-4 text-gray-900">Generated Scenarios</h2>
              {scenarios.map((scenario, index) => (
                <div key={index} className="mb-6 p-4 border border-gray-200 rounded-lg">
                  <h3 className="text-xl font-semibold mb-2">{scenario.scenario}</h3>
                  <p className="text-gray-600 mb-2">{scenario.reason}</p>
                  <div className="mb-2">
                    <strong>Hashtags:</strong>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {scenario.hashtags.map((tag, tagIndex) => (
                        <span key={tagIndex} className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-sm">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="mb-2">
                    <strong>Content Guidance:</strong>
                    <ul className="list-disc list-inside mt-1">
                      <li><strong>Main Theme:</strong> {scenario.content_guidance.main_theme}</li>
                      <li><strong>Hook:</strong> {scenario.content_guidance.hook}</li>
                      <li><strong>Key Points:</strong> {scenario.content_guidance.key_points.join(', ')}</li>
                      <li><strong>Visuals:</strong> {scenario.content_guidance.visuals.join(', ')}</li>
                      <li><strong>Call to Action:</strong> {scenario.content_guidance.call_to_action}</li>
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default HashtagGenerator;