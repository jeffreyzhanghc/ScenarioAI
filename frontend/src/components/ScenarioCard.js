import React, { useState } from 'react';
import { Hash, ChevronDown, ChevronUp } from 'lucide-react';

const ScenarioCard = ({ scenario, isSelected, onClick }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleExpand = (e) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  return (
    <div 
      className={`p-6 rounded-xl cursor-pointer transition-all duration-300 ${
        isSelected 
          ? 'bg-gradient-to-br from-indigo-200 to-purple-200 shadow-md' 
          : 'bg-white hover:bg-gradient-to-br hover:from-indigo-50 hover:to-purple-50'
      }`}
      onClick={onClick}
    >
      <h3 className={`text-xl font-bold mb-3 ${isSelected ? 'text-indigo-900' : 'text-gray-800'}`}>
        {scenario.scenario}
      </h3>
      <p className={`text-sm mb-4 line-clamp-2 ${isSelected ? 'text-indigo-700' : 'text-gray-600'}`}>
        {scenario.reason}
      </p>
      <div className="flex flex-wrap gap-2">
        {(isExpanded ? scenario.hashtags : scenario.hashtags.slice(0, 3)).map((tag, index) => (
          <span key={index} className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
            isSelected ? 'bg-indigo-300 text-indigo-800' : 'bg-indigo-100 text-indigo-600'
          }`}>
            {tag}
          </span>
        ))}
        {!isExpanded && scenario.hashtags.length > 3 && (
          <button
            onClick={toggleExpand}
            className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
              isSelected ? 'bg-purple-300 text-purple-800' : 'bg-purple-100 text-purple-600'
            } hover:bg-purple-200 transition-colors duration-300`}
          >
            +{scenario.hashtags.length - 3} more
            <ChevronDown size={14} className="ml-1" />
          </button>
        )}
        {isExpanded && (
          <button
            onClick={toggleExpand}
            className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
              isSelected ? 'bg-purple-300 text-purple-800' : 'bg-purple-100 text-purple-600'
            } hover:bg-purple-200 transition-colors duration-300`}
          >
            Show less
            <ChevronUp size={14} className="ml-1" />
          </button>
        )}
      </div>
    </div>
  );
};

export default ScenarioCard;