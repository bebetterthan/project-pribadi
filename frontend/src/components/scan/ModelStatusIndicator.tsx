'use client';

import React, { useEffect, useState } from 'react';
import { Zap, Brain, TrendingUp, DollarSign, Activity } from 'lucide-react';

interface ModelStatusIndicatorProps {
  currentModel: 'flash' | 'pro' | 'transition';
  status: string;
  activity?: string;
  transitionMessage?: string;
}

export const ModelStatusIndicator: React.FC<ModelStatusIndicatorProps> = ({
  currentModel,
  status,
  activity,
  transitionMessage
}) => {
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (currentModel === 'transition') {
      setIsAnimating(true);
      const timer = setTimeout(() => setIsAnimating(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [currentModel]);

  // Flash Active State
  if (currentModel === 'flash') {
    return (
      <div className="relative overflow-hidden rounded-xl border border-blue-500/30 bg-gradient-to-r from-blue-900/30 via-blue-800/20 to-cyan-900/30 shadow-lg shadow-blue-500/10">
        {/* Animated background glow */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute inset-0 animate-pulse bg-gradient-to-r from-transparent via-blue-500/30 to-transparent" />
        </div>
        
        <div className="relative px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Left: Model Info */}
            <div className="flex items-center space-x-4">
              {/* Icon with pulse animation */}
              <div className="relative">
                <div className="absolute inset-0 bg-blue-500 rounded-full animate-ping opacity-20" />
                <div className="relative bg-blue-500/20 p-3 rounded-full border border-blue-400/30">
                  <Zap className="h-6 w-6 text-blue-300" strokeWidth={2.5} />
                </div>
              </div>
              
              {/* Model Details */}
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <h3 className="text-lg font-bold text-blue-200">⚡ FLASH AI 2.5</h3>
                  <div className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-blue-500/20 border border-blue-400/30">
                    <Activity className="h-3 w-3 text-blue-300 animate-pulse" />
                    <span className="text-xs font-semibold text-blue-300 uppercase">Active</span>
                  </div>
                </div>
                <p className="text-sm text-blue-300/80">{status}</p>
                {activity && (
                  <p className="text-xs text-blue-400/60 mt-1 flex items-center space-x-1">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                    <span>{activity}</span>
                  </p>
                )}
              </div>
            </div>

            {/* Right: Characteristics */}
            <div className="flex flex-col items-end space-y-1">
              <div className="flex items-center space-x-2 text-blue-300">
                <TrendingUp className="h-4 w-4" />
                <span className="text-sm font-semibold">Fast & Efficient</span>
              </div>
              <div className="flex items-center space-x-2 text-blue-400/70">
                <DollarSign className="h-3.5 w-3.5" />
                <span className="text-xs">Low Cost • $0.0001/call</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Pro Active State
  if (currentModel === 'pro') {
    return (
      <div className="relative overflow-hidden rounded-xl border border-purple-500/30 bg-gradient-to-r from-purple-900/30 via-purple-800/20 to-pink-900/30 shadow-lg shadow-purple-500/10">
        {/* Animated wave effect */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 animate-pulse bg-gradient-to-r from-transparent via-purple-500/40 to-transparent" style={{ animationDuration: '3s' }} />
        </div>
        
        <div className="relative px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Left: Model Info */}
            <div className="flex items-center space-x-4">
              {/* Icon with glow */}
              <div className="relative">
                <div className="absolute inset-0 bg-purple-500 rounded-full blur-md opacity-40 animate-pulse" style={{ animationDuration: '2s' }} />
                <div className="relative bg-purple-500/20 p-3 rounded-full border border-purple-400/30">
                  <Brain className="h-6 w-6 text-purple-300" strokeWidth={2.5} />
                </div>
              </div>
              
              {/* Model Details */}
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <h3 className="text-lg font-bold text-purple-200">🧠 PRO AI 2.5</h3>
                  <div className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-purple-500/20 border border-purple-400/30">
                    <Activity className="h-3 w-3 text-purple-300 animate-pulse" style={{ animationDuration: '2s' }} />
                    <span className="text-xs font-semibold text-purple-300 uppercase">Analyzing</span>
                  </div>
                </div>
                <p className="text-sm text-purple-300/80">{status}</p>
                {activity && (
                  <p className="text-xs text-purple-400/60 mt-1 flex items-center space-x-1">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" style={{ animationDuration: '1.5s' }} />
                    <span>{activity}</span>
                  </p>
                )}
              </div>
            </div>

            {/* Right: Characteristics */}
            <div className="flex flex-col items-end space-y-1">
              <div className="flex items-center space-x-2 text-purple-300">
                <Brain className="h-4 w-4" />
                <span className="text-sm font-semibold">Deep & Strategic</span>
              </div>
              <div className="flex items-center space-x-2 text-purple-400/70">
                <DollarSign className="h-3.5 w-3.5" />
                <span className="text-xs">Premium Quality • $0.001/call</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Transition State (Flash → Pro or Pro → Flash)
  if (currentModel === 'transition') {
    return (
      <div className="relative overflow-hidden rounded-xl border border-indigo-500/30 bg-gradient-to-r from-blue-900/30 via-purple-800/30 to-purple-900/30 shadow-lg">
        {/* Sliding gradient animation */}
        <div className="absolute inset-0 opacity-30">
          <div 
            className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 animate-pulse"
            style={{ animationDuration: '1s' }}
          />
        </div>
        
        <div className="relative px-6 py-4">
          <div className="flex items-center justify-center space-x-4">
            {/* Morphing icons */}
            <div className="relative">
              <Zap className={`h-6 w-6 text-blue-300 absolute transition-all duration-500 ${isAnimating ? 'opacity-0 scale-50' : 'opacity-100 scale-100'}`} />
              <Brain className={`h-6 w-6 text-purple-300 absolute transition-all duration-500 ${isAnimating ? 'opacity-100 scale-100' : 'opacity-0 scale-50'}`} />
            </div>
            
            <div className="text-center">
              <div className="flex items-center space-x-2 mb-1">
                <div className="flex space-x-1">
                  <span className="inline-block w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="inline-block w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="inline-block w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-sm font-semibold text-indigo-200 uppercase tracking-wide">
                  Model Transition
                </span>
              </div>
              <p className="text-sm text-indigo-300/80">
                {transitionMessage || 'Escalating to Pro for deep analysis...'}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

