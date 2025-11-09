/**
 * CostTracker - Display token usage and estimated API costs
 * Transparency feature for showing resource consumption
 */

import React from 'react';
import { DollarSign, Zap, TrendingUp, Info } from 'lucide-react';

interface CostTrackerProps {
  metadata?: {
    total_tokens?: number;
    prompt_tokens?: number;
    completion_tokens?: number;
    estimated_cost?: number;
    model_calls?: number;
    flash_calls?: number;
    pro_calls?: number;
  };
}

export function CostTracker({ metadata }: CostTrackerProps) {
  if (!metadata || (!metadata.total_tokens && !metadata.model_calls)) {
    return null;
  }

  const totalTokens = metadata.total_tokens || 0;
  const promptTokens = metadata.prompt_tokens || 0;
  const completionTokens = metadata.completion_tokens || 0;
  const estimatedCost = metadata.estimated_cost || 0;
  const totalCalls = (metadata.flash_calls || 0) + (metadata.pro_calls || 0);

  return (
    <div className="bg-gradient-to-br from-amber-500/5 to-orange-500/5 border border-amber-500/20 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center space-x-2 mb-4">
        <DollarSign className="w-4 h-4 text-amber-400" />
        <h3 className="text-sm font-semibold text-amber-300">Cost & Token Usage</h3>
        <div className="flex-1" />
        <div className="group relative">
          <Info className="w-4 h-4 text-gray-500 cursor-help" />
          <div className="absolute right-0 bottom-full mb-2 hidden group-hover:block w-64 bg-gray-900 border border-gray-700 rounded-lg p-3 text-xs text-gray-300 shadow-xl z-50">
            <p className="mb-2">
              Token usage and estimated costs based on Google Gemini API pricing:
            </p>
            <ul className="space-y-1 text-gray-400">
              <li>• Flash: $0.075 / 1M tokens</li>
              <li>• Pro: $1.25 / 1M tokens (input)</li>
              <li>• Pro: $5.00 / 1M tokens (output)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3">
        {/* Total Tokens */}
        <div className="bg-black/20 rounded-lg p-3">
          <div className="flex items-center space-x-2 mb-1">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-xs text-gray-500">Total Tokens</span>
          </div>
          <p className="text-lg font-semibold text-amber-300">
            {totalTokens.toLocaleString()}
          </p>
          {promptTokens > 0 && completionTokens > 0 && (
            <p className="text-xs text-gray-600 mt-1">
              {promptTokens.toLocaleString()} in • {completionTokens.toLocaleString()} out
            </p>
          )}
        </div>

        {/* Estimated Cost */}
        <div className="bg-black/20 rounded-lg p-3">
          <div className="flex items-center space-x-2 mb-1">
            <DollarSign className="w-3.5 h-3.5 text-green-400" />
            <span className="text-xs text-gray-500">Estimated Cost</span>
          </div>
          <p className="text-lg font-semibold text-green-300">
            ${estimatedCost.toFixed(4)}
          </p>
          {totalTokens > 0 && (
            <p className="text-xs text-gray-600 mt-1">
              ${(estimatedCost / totalTokens * 1000).toFixed(2)}/1K tokens
            </p>
          )}
        </div>

        {/* Model Calls */}
        {totalCalls > 0 && (
          <>
            <div className="bg-black/20 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-xs">⚡</span>
                <span className="text-xs text-gray-500">Flash Calls</span>
              </div>
              <p className="text-lg font-semibold text-blue-300">
                {metadata.flash_calls || 0}
              </p>
              <p className="text-xs text-gray-600 mt-1">Fast responses</p>
            </div>

            <div className="bg-black/20 rounded-lg p-3">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-xs">🧠</span>
                <span className="text-xs text-gray-500">Pro Calls</span>
              </div>
              <p className="text-lg font-semibold text-purple-300">
                {metadata.pro_calls || 0}
              </p>
              <p className="text-xs text-gray-600 mt-1">Deep reasoning</p>
            </div>
          </>
        )}
      </div>

      {/* Efficiency Indicator */}
      {totalCalls > 1 && (
        <div className="mt-3 pt-3 border-t border-amber-500/10">
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>
              Hybrid routing saved ~{Math.round((metadata.flash_calls || 0) / totalCalls * 100)}% on costs
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

