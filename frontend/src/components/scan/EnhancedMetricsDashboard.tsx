'use client';

import React from 'react';
import { 
  Zap, 
  Brain, 
  DollarSign, 
  Clock, 
  Target, 
  TrendingUp,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';

interface ModelMetrics {
  flash_calls: number;
  pro_calls: number;
  flash_cost: number;
  pro_cost: number;
  total_cost: number;
  flash_percentage: number;
  pro_percentage: number;
}

interface ScanMetrics {
  duration: number;
  tools_executed: number;
  targets_scanned: number;
  findings_total: number;
  findings_critical: number;
  findings_high: number;
  time_saved_by_validation?: number;
  cost_optimized_percentage?: number;
}

interface EnhancedMetricsDashboardProps {
  modelMetrics: ModelMetrics;
  scanMetrics: ScanMetrics;
  budgetLimit?: number;
}

export const EnhancedMetricsDashboard: React.FC<EnhancedMetricsDashboardProps> = ({
  modelMetrics,
  scanMetrics,
  budgetLimit = 0.05
}) => {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const budgetUsedPercentage = (modelMetrics.total_cost / budgetLimit) * 100;
  const isOptimal = modelMetrics.flash_percentage >= 75 && modelMetrics.flash_percentage <= 90;

  return (
    <div className="space-y-6">
      {/* AI Model Usage */}
      <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 border border-gray-700 rounded-xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-lg border border-blue-500/30">
              <Brain className="h-6 w-6 text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">AI MODEL USAGE</h3>
              <p className="text-xs text-gray-400">Dual-model efficiency tracking</p>
            </div>
          </div>
          
          {isOptimal && (
            <div className="flex items-center space-x-2 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-lg">
              <CheckCircle2 className="h-4 w-4 text-green-400" />
              <span className="text-xs font-semibold text-green-300">Optimal Balance</span>
            </div>
          )}
        </div>

        {/* Model Call Stats */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* Flash Stats */}
          <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Zap className="h-5 w-5 text-blue-400" />
              <span className="text-sm font-semibold text-blue-300">Flash AI 2.5</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-baseline">
                <span className="text-xs text-gray-400">Calls</span>
                <span className="text-2xl font-bold text-blue-300">{modelMetrics.flash_calls}</span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-xs text-gray-400">Cost</span>
                <span className="text-sm font-semibold text-blue-400">${modelMetrics.flash_cost.toFixed(4)}</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2 mt-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-cyan-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${modelMetrics.flash_percentage}%` }}
                />
              </div>
              <div className="text-xs text-gray-500 text-right">
                {modelMetrics.flash_percentage.toFixed(1)}% of calls
              </div>
            </div>
          </div>

          {/* Pro Stats */}
          <div className="bg-purple-500/5 border border-purple-500/20 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Brain className="h-5 w-5 text-purple-400" />
              <span className="text-sm font-semibold text-purple-300">Pro AI 2.5</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-baseline">
                <span className="text-xs text-gray-400">Calls</span>
                <span className="text-2xl font-bold text-purple-300">{modelMetrics.pro_calls}</span>
              </div>
              <div className="flex justify-between items-baseline">
                <span className="text-xs text-gray-400">Cost</span>
                <span className="text-sm font-semibold text-purple-400">${modelMetrics.pro_cost.toFixed(4)}</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2 mt-2">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${modelMetrics.pro_percentage}%` }}
                />
              </div>
              <div className="text-xs text-gray-500 text-right">
                {modelMetrics.pro_percentage.toFixed(1)}% of calls
              </div>
            </div>
          </div>
        </div>

        {/* Cost Breakdown */}
        <div className="bg-gradient-to-r from-green-900/20 to-emerald-900/20 border border-green-500/30 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <DollarSign className="h-5 w-5 text-green-400" />
              <span className="font-semibold text-green-300">Total Cost</span>
            </div>
            <span className="text-2xl font-bold text-green-400">
              ${modelMetrics.total_cost.toFixed(4)}
            </span>
          </div>
          
          {/* Budget Progress */}
          <div>
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>Budget Used</span>
              <span>{budgetUsedPercentage.toFixed(1)}% of ${budgetLimit.toFixed(2)}</span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
              <div 
                className={`h-2 rounded-full transition-all duration-500 ${
                  budgetUsedPercentage > 80 
                    ? 'bg-gradient-to-r from-red-500 to-orange-500' 
                    : 'bg-gradient-to-r from-green-500 to-emerald-500'
                }`}
                style={{ width: `${Math.min(budgetUsedPercentage, 100)}%` }}
              />
            </div>
          </div>

          {/* Cost Optimization Note */}
          {scanMetrics.cost_optimized_percentage && (
            <div className="mt-3 text-xs text-green-400/80 flex items-center space-x-2">
              <TrendingUp className="h-3 w-3" />
              <span>
                ~{scanMetrics.cost_optimized_percentage}% cost savings through dual-model optimization
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Scan Performance */}
      <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 border border-gray-700 rounded-xl p-6 shadow-xl">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-lg border border-cyan-500/30">
            <Target className="h-6 w-6 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">SCAN PERFORMANCE</h3>
            <p className="text-xs text-gray-400">Execution metrics and efficiency</p>
          </div>
        </div>

        {/* Performance Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Duration */}
          <div className="bg-black/20 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Clock className="h-4 w-4 text-cyan-400" />
              <span className="text-xs text-gray-400">Duration</span>
            </div>
            <div className="text-2xl font-bold text-white">
              {formatTime(scanMetrics.duration)}
            </div>
          </div>

          {/* Tools Executed */}
          <div className="bg-black/20 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Zap className="h-4 w-4 text-blue-400" />
              <span className="text-xs text-gray-400">Tools</span>
            </div>
            <div className="text-2xl font-bold text-white">
              {scanMetrics.tools_executed}
            </div>
          </div>

          {/* Targets Scanned */}
          <div className="bg-black/20 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="h-4 w-4 text-purple-400" />
              <span className="text-xs text-gray-400">Targets</span>
            </div>
            <div className="text-2xl font-bold text-white">
              {scanMetrics.targets_scanned}
            </div>
          </div>

          {/* Total Findings */}
          <div className="bg-black/20 border border-gray-700 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <AlertCircle className="h-4 w-4 text-orange-400" />
              <span className="text-xs text-gray-400">Findings</span>
            </div>
            <div className="text-2xl font-bold text-white">
              {scanMetrics.findings_total}
            </div>
          </div>
        </div>

        {/* Findings Breakdown */}
        <div className="mt-6 bg-gradient-to-r from-red-900/10 to-orange-900/10 border border-red-500/20 rounded-lg p-4">
          <div className="text-sm font-semibold text-gray-300 mb-3">Security Findings Breakdown</div>
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-red-500"></span>
              <span className="text-xs text-gray-400">Critical:</span>
              <span className="text-sm font-semibold text-red-400">{scanMetrics.findings_critical}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-orange-500"></span>
              <span className="text-xs text-gray-400">High:</span>
              <span className="text-sm font-semibold text-orange-400">{scanMetrics.findings_high}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-3 h-3 rounded-full bg-gray-500"></span>
              <span className="text-xs text-gray-400">Other:</span>
              <span className="text-sm font-semibold text-gray-400">
                {scanMetrics.findings_total - scanMetrics.findings_critical - scanMetrics.findings_high}
              </span>
            </div>
          </div>
        </div>

        {/* Efficiency Indicators */}
        {scanMetrics.time_saved_by_validation && (
          <div className="mt-4 bg-green-500/10 border border-green-500/30 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-green-300 text-sm">
                <TrendingUp className="h-4 w-4" />
                <span className="font-semibold">Efficiency Gains</span>
              </div>
              <span className="text-green-400 font-bold">
                ~{scanMetrics.time_saved_by_validation}% time saved
              </span>
            </div>
            <p className="text-xs text-green-400/70 mt-2">
              Through intelligent domain validation and filtering
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

