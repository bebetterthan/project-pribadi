'use client';

import React from 'react';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

interface ScanProgressProps {
  currentTool?: string;
  completedTools: string[];
  allTools: string[];
}

export const ScanProgress: React.FC<ScanProgressProps> = ({
  currentTool,
  completedTools,
  allTools,
}) => {
  const getToolStatus = (tool: string) => {
    if (completedTools.includes(tool)) return 'completed';
    if (tool === currentTool) return 'running';
    return 'pending';
  };

  const progressPercentage = (completedTools.length / allTools.length) * 100;

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <div>
        <div className="flex justify-between text-sm text-gray-300 mb-3">
          <span className="font-medium">Scan Progress</span>
          <span className="text-green-400 font-semibold">{Math.round(progressPercentage)}%</span>
        </div>
        <div className="h-3 bg-[#1a1a1a] rounded-full overflow-hidden border border-[#3a3a3a]">
          <div
            className="h-full bg-gradient-to-r from-green-600 to-green-500 transition-all duration-500 ease-out shadow-lg shadow-green-500/20"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Tool Status List */}
      <div className="space-y-2 pt-2">
        {allTools.map((tool) => {
          const status = getToolStatus(tool);
          return (
            <div
              key={tool}
              className="flex items-center space-x-3 p-3 rounded-lg bg-[#1a1a1a] border border-[#3a3a3a] hover:border-[#4a4a4a] transition-colors"
            >
              {status === 'completed' && (
                <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
              )}
              {status === 'running' && (
                <Loader2 className="h-5 w-5 text-blue-400 animate-spin flex-shrink-0" />
              )}
              {status === 'pending' && (
                <Circle className="h-5 w-5 text-gray-600 flex-shrink-0" />
              )}
              <span
                className={`capitalize font-medium flex-1 ${
                  status === 'completed'
                    ? 'text-green-400'
                    : status === 'running'
                    ? 'text-blue-400'
                    : 'text-gray-500'
                }`}
              >
                {tool}
              </span>
              {status === 'running' && (
                <span className="text-xs text-blue-400 bg-blue-500/10 px-2 py-1 rounded">
                  Running...
                </span>
              )}
              {status === 'completed' && (
                <span className="text-xs text-green-400 bg-green-500/10 px-2 py-1 rounded">
                  Completed
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
