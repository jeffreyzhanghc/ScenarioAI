import React, { useState } from 'react';
import {
  Search,
  Hash,
  Zap,
  Video,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import ScenarioCard from './ScenarioCard';

const API_BASE_URL = 'http://127.0.0.1:8000';

const CollapsibleSection = ({ title, children }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border-t border-gray-300 pt-4">
      <button
        className="flex justify-between items-center w-full text-left focus:outline-none"
        onClick={() => setIsOpen(!isOpen)}
      >
        <h3 className="text-lg font-medium text-gray-800 flex items-center">
          <Video className="mr-2 text-blue-500" size={20} />
          {title}
        </h3>
        {isOpen ? (
          <ChevronUp className="text-blue-500" size={20} />
        ) : (
          <ChevronDown className="text-blue-500" size={20} />
        )}
      </button>
      {isOpen && <div className="mt-4">{children}</div>}
    </div>
  );
};

const ScenarioDetail = ({ scenario }) => (
  <div className="bg-white rounded-lg shadow-md overflow-hidden">
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-semibold text-gray-900 border-b border-gray-200 pb-4">
        {scenario.scenario}
      </h2>

      <div className="bg-blue-50 p-4 rounded-lg">
        <h3 className="text-lg font-medium mb-3 text-blue-600 flex items-center">
          <Zap className="mr-2" size={20} />
          Reason
        </h3>
        <p className="text-gray-700">{scenario.reason}</p>
      </div>

      <div>
        <h3 className="text-lg font-medium mb-3 text-blue-600 flex items-center">
          <Hash className="mr-2" size={20} />
          Hashtags
        </h3>
        <div className="flex flex-wrap gap-2">
          {scenario.hashtags.map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors duration-300"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium text-blue-600">Content Guidance</h3>
        {Object.entries(scenario.content_guidance).map(([key, value], idx) => (
          <div key={idx} className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-500 mb-2 capitalize">
              {key.replace('_', ' ')}
            </h4>
            {Array.isArray(value) ? (
              <ul className="list-disc list-inside text-gray-800 space-y-1">
                {value.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-800">{value}</p>
            )}
          </div>
        ))}
      </div>

      <CollapsibleSection title="Related TikTok Videos">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="aspect-w-9 aspect-h-16 bg-gray-200 rounded-lg overflow-hidden">
            <iframe
              src="https://www.tiktok.com/oembed?url=https://www.tiktok.com/@chrisandjasmin/video/7353284590523436331"
              allowFullScreen
              className="w-full h-full"
            ></iframe>
          </div>
          {/* Add more video embeds as needed */}
        </div>
      </CollapsibleSection>
    </div>
  </div>
);

const ScenarioGenerator = () => {
  const [keywords, setKeywords] = useState('');
  const [scenarios, setScenarios] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedScenario, setSelectedScenario] = useState(null);

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
          hashtags: [],
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate scenarios');
      }

      const data = await response.json();
      setScenarios(data.scenarios);
      setSelectedScenario(data.scenarios[0]);
    } catch (error) {
      console.error('Error:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm py-4">
        <div className="container mx-auto px-6">
          <h1 className="text-3xl font-bold text-center text-blue-600">
            Scenario AI Generator
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Search Form */}
        <form
          onSubmit={handleSubmit}
          className="max-w-3xl mx-auto mb-10"
        >
          <div className="flex items-center bg-white rounded-full shadow-lg p-2">
            <input
              type="text"
              className="flex-grow px-4 py-2 bg-transparent focus:outline-none text-gray-800"
              placeholder="Enter keywords for your content"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              required
            />
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-full transition duration-300 flex items-center"
              disabled={isLoading}
            >
              {isLoading ? 'Generating...' : 'Generate'}
              <Search className="ml-2" size={20} />
            </button>
          </div>
        </form>

        {/* Error Message */}
        {error && (
          <div className="max-w-3xl mx-auto mt-4 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200">
            Error: {error}
          </div>
        )}

        {/* Scenarios and Details */}
        {scenarios.length > 0 && (
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Scenario List */}
            <div
              className="lg:w-1/3 space-y-4 overflow-y-auto"
              style={{
                maxHeight: 'calc(100vh - 200px)',
              }}
            >
              {scenarios.map((scenario, index) => (
                <ScenarioCard
                  key={index}
                  scenario={scenario}
                  isSelected={selectedScenario === scenario}
                  onClick={() => setSelectedScenario(scenario)}
                />
              ))}
            </div>

            {/* Scenario Details */}
            <div
              className="lg:w-2/3 overflow-y-auto"
              style={{
                maxHeight: 'calc(100vh - 200px)',
              }}
            >
              {selectedScenario && (
                <ScenarioDetail scenario={selectedScenario} />
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default ScenarioGenerator;
