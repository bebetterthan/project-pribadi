import React from 'react';
import { Brain, Zap, TrendingUp, DollarSign } from 'lucide-react';

interface ModelAttributionProps {
  model: 'flash' | 'pro';
  phase: string;
  reasoning?: string;
}

export const ModelAttribution: React.FC<ModelAttributionProps> = ({ model, phase, reasoning }) => {
  const isFlash = model === 'flash';
  
  return (
    <div className={`flex items-start space-x-3 p-3 rounded-lg border ${
      isFlash 
        ? 'bg-blue-900/20 border-blue-700/30' 
        : 'bg-purple-900/20 border-purple-700/30'
    }`}>
      {isFlash ? (
        <Zap className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
      ) : (
        <Brain className="h-5 w-5 text-purple-400 flex-shrink-0 mt-0.5" />
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2 mb-1">
          <span className={`font-semibold text-sm ${
            isFlash ? 'text-blue-300' : 'text-purple-300'
          }`}>
            {isFlash ? 'Flash AI 2.5' : 'Pro AI 2.5'}
          </span>
          <span className="text-gray-500 text-xs">•</span>
          <span className="text-gray-400 text-xs">{phase}</span>
        </div>
        {reasoning && (
          <p className="text-gray-300 text-sm mt-1">{reasoning}</p>
        )}
        <div className="flex items-center space-x-2 mt-2 text-xs text-gray-500">
          <TrendingUp className="h-3 w-3" />
          <span>{isFlash ? 'Fast & Efficient' : 'Deep & Strategic'}</span>
          <span>•</span>
          <DollarSign className="h-3 w-3" />
          <span>{isFlash ? '$0.0001/call' : '$0.001/call'}</span>
        </div>
      </div>
    </div>
  );
};

interface CostTrackerProps {
  flashCalls: number;
  proCalls: number;
}

export const CostTracker: React.FC<CostTrackerProps> = ({ flashCalls, proCalls }) => {
  const flashCost = flashCalls * 0.0001;
  const proCost = proCalls * 0.001;
  const totalCost = flashCost + proCost;
  const totalCalls = flashCalls + proCalls;
  
  const flashPercentage = totalCalls > 0 ? (flashCalls / totalCalls) * 100 : 0;
  const proPercentage = totalCalls > 0 ? (proCalls / totalCalls) * 100 : 0;
  
  return (
    <div className="bg-[#1a1a1a] border border-[#3a3a3a] rounded-lg p-4 shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-white flex items-center">
          <DollarSign className="h-5 w-5 mr-2 text-green-400" />
          Cost Tracking
        </h3>
        <span className="text-2xl font-bold text-green-400">
          ${totalCost.toFixed(4)}
        </span>
      </div>
      
      <div className="space-y-3">
        {/* Flash Stats */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-blue-300 flex items-center">
              <Zap className="h-3 w-3 mr-1" />
              Flash AI
            </span>
            <span className="text-gray-400">{flashCalls} calls • ${flashCost.toFixed(4)}</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${flashPercentage}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{flashPercentage.toFixed(1)}% of calls</p>
        </div>
        
        {/* Pro Stats */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-purple-300 flex items-center">
              <Brain className="h-3 w-3 mr-1" />
              Pro AI
            </span>
            <span className="text-gray-400">{proCalls} calls • ${proCost.toFixed(4)}</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-purple-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${proPercentage}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">{proPercentage.toFixed(1)}% of calls</p>
        </div>
      </div>
      
      <div className="mt-4 pt-3 border-t border-gray-700">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Total AI Calls:</span>
          <span className="text-white font-semibold">{totalCalls}</span>
        </div>
        <div className="flex justify-between text-sm mt-1">
          <span className="text-gray-400">Efficiency:</span>
          <span className="text-green-400 font-semibold">
            {flashPercentage >= 80 ? 'Excellent' : flashPercentage >= 60 ? 'Good' : 'Moderate'}
          </span>
        </div>
      </div>
    </div>
  );
};

