'use client';

import React from 'react';
import { CheckCircle2, Clock, Loader2, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';

// Overall Scan Progress
interface OverallProgressProps {
  percentage: number;
  phase: string;
  currentTool?: string;
  completedTools: number;
  totalTools: number;
  elapsedTime: number;
  estimatedTimeRemaining?: number;
}

export const OverallProgress: React.FC<OverallProgressProps> = ({
  percentage,
  phase,
  currentTool,
  completedTools,
  totalTools,
  elapsedTime,
  estimatedTimeRemaining
}) => {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 border border-gray-700 rounded-xl p-6 shadow-xl">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xl font-bold text-white">SCAN PROGRESS</h3>
          <span className="text-3xl font-bold text-cyan-400">{percentage}%</span>
        </div>
        
        {/* Progress Bar */}
        <div className="relative w-full h-4 bg-gray-800 rounded-full overflow-hidden border border-gray-700">
          <div 
            className="absolute inset-0 bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 transition-all duration-500 ease-out"
            style={{ width: `${percentage}%` }}
          >
            {/* Animated shimmer effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
          </div>
        </div>
      </div>

      {/* Status Info */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <div className="text-gray-400 mb-1">Current Phase</div>
          <div className="text-white font-semibold">{phase}</div>
        </div>
        <div>
          <div className="text-gray-400 mb-1">Current Tool</div>
          <div className="text-cyan-400 font-mono">{currentTool || 'Initializing...'}</div>
        </div>
        <div>
          <div className="text-gray-400 mb-1">Tools Progress</div>
          <div className="text-white font-semibold">{completedTools} of {totalTools} completed</div>
        </div>
        <div>
          <div className="text-gray-400 mb-1">Time</div>
          <div className="text-white">
            <span className="font-semibold">{formatTime(elapsedTime)}</span> elapsed
            {estimatedTimeRemaining && (
              <span className="text-gray-500"> • ~{formatTime(estimatedTimeRemaining)} remaining</span>
            )}
          </div>
        </div>
      </div>

      {/* Animated shimmer keyframes */}
      <style jsx>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  );
};

// Phase Progress
interface Phase {
  id: string;
  name: string;
  status: 'completed' | 'in_progress' | 'pending';
  toolsCompleted?: number;
  totalTools?: number;
  currentTool?: string;
  findings?: number;
}

interface PhaseProgressProps {
  phases: Phase[];
}

export const PhaseProgress: React.FC<PhaseProgressProps> = ({ phases }) => {
  const [expandedPhase, setExpandedPhase] = React.useState<string | null>(
    phases.find(p => p.status === 'in_progress')?.id || null
  );

  const getPhaseIcon = (status: Phase['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-400" />;
      case 'in_progress':
        return <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getPhaseColor = (status: Phase['status']) => {
    switch (status) {
      case 'completed':
        return 'border-green-500/30 bg-green-900/10';
      case 'in_progress':
        return 'border-blue-500/30 bg-blue-900/20';
      case 'pending':
        return 'border-gray-700 bg-gray-900/20';
    }
  };

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-bold text-white mb-4">SCAN PHASES</h3>
      
      {phases.map((phase, index) => {
        const isExpanded = expandedPhase === phase.id;
        const canExpand = phase.status !== 'pending';
        
        return (
          <div 
            key={phase.id}
            className={`border rounded-lg overflow-hidden transition-all ${getPhaseColor(phase.status)}`}
          >
            {/* Phase Header */}
            <button
              onClick={() => canExpand && setExpandedPhase(isExpanded ? null : phase.id)}
              className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors disabled:cursor-not-allowed"
              disabled={!canExpand}
            >
              <div className="flex items-center space-x-3">
                {getPhaseIcon(phase.status)}
                <div className="text-left">
                  <div className="font-semibold text-white flex items-center space-x-2">
                    <span>Phase {index + 1}: {phase.name}</span>
                    {phase.status === 'completed' && (
                      <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-300 rounded border border-green-500/30">
                        COMPLETE
                      </span>
                    )}
                    {phase.status === 'in_progress' && (
                      <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-300 rounded border border-blue-500/30 animate-pulse">
                        IN PROGRESS
                      </span>
                    )}
                    {phase.status === 'pending' && (
                      <span className="px-2 py-0.5 text-xs bg-gray-500/20 text-gray-400 rounded border border-gray-500/30">
                        PENDING
                      </span>
                    )}
                  </div>
                  {phase.status !== 'pending' && phase.toolsCompleted !== undefined && (
                    <div className="text-xs text-gray-400 mt-1">
                      {phase.toolsCompleted} of {phase.totalTools} tools completed
                      {phase.findings !== undefined && ` • ${phase.findings} findings`}
                    </div>
                  )}
                </div>
              </div>
              
              {canExpand && (
                isExpanded ? (
                  <ChevronUp className="h-5 w-5 text-gray-400" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-gray-400" />
                )
              )}
            </button>

            {/* Phase Details (Expanded) */}
            {isExpanded && phase.status === 'in_progress' && (
              <div className="px-4 pb-4 border-t border-white/10 animate-in slide-in-from-top-2 duration-200">
                <div className="pt-3 space-y-2">
                  {phase.currentTool && (
                    <div className="flex items-center space-x-2 text-sm">
                      <Loader2 className="h-4 w-4 text-blue-400 animate-spin" />
                      <span className="text-gray-300">Currently running:</span>
                      <span className="text-blue-400 font-mono">{phase.currentTool}</span>
                    </div>
                  )}
                  
                  {/* Progress bar for phase */}
                  {phase.toolsCompleted !== undefined && phase.totalTools !== undefined && (
                    <div className="mt-3">
                      <div className="flex justify-between text-xs text-gray-400 mb-1">
                        <span>Phase Progress</span>
                        <span>{Math.round((phase.toolsCompleted / phase.totalTools) * 100)}%</span>
                      </div>
                      <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
                          style={{ width: `${(phase.toolsCompleted / phase.totalTools) * 100}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {isExpanded && phase.status === 'completed' && phase.findings !== undefined && (
              <div className="px-4 pb-4 border-t border-white/10 animate-in slide-in-from-top-2 duration-200">
                <div className="pt-3 text-sm text-gray-300">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="h-4 w-4 text-green-400" />
                    <span>{phase.toolsCompleted} tools executed successfully</span>
                  </div>
                  <div className="mt-2 px-3 py-2 bg-green-500/10 border border-green-500/30 rounded text-green-300">
                    📊 {phase.findings} findings discovered in this phase
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// Tool-Specific Progress
interface ToolProgress {
  tool: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress?: number;
  current?: string;
  total?: number;
  completed?: number;
  elapsedTime?: number;
  estimatedTime?: number;
}

interface ToolProgressCardProps {
  toolProgress: ToolProgress;
}

export const ToolProgressCard: React.FC<ToolProgressCardProps> = ({ toolProgress }) => {
  const { tool, status, progress, current, total, completed, elapsedTime, estimatedTime } = toolProgress;

  const getStatusColor = () => {
    switch (status) {
      case 'running':
        return 'border-blue-500/30 bg-blue-900/10';
      case 'completed':
        return 'border-green-500/30 bg-green-900/10';
      case 'failed':
        return 'border-red-500/30 bg-red-900/10';
      case 'queued':
      default:
        return 'border-gray-700 bg-gray-900/10';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-400" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-400" />;
      case 'queued':
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <div className={`border rounded-lg p-4 ${getStatusColor()}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h4 className="font-semibold text-white">{tool.toUpperCase()}</h4>
            {current && (
              <p className="text-xs text-gray-400 mt-1">{current}</p>
            )}
          </div>
        </div>
        
        {elapsedTime !== undefined && (
          <div className="text-xs text-gray-400">
            {Math.round(elapsedTime)}s
            {estimatedTime && status === 'running' && (
              <span className="text-gray-600"> / ~{Math.round(estimatedTime)}s</span>
            )}
          </div>
        )}
      </div>

      {/* Progress for countable tasks */}
      {progress !== undefined && status === 'running' && (
        <div>
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Item count progress */}
      {completed !== undefined && total !== undefined && status === 'running' && (
        <div className="mt-2 text-xs text-gray-400">
          {completed} of {total} items processed
        </div>
      )}

      {/* Indeterminate spinner for unknown duration */}
      {progress === undefined && status === 'running' && (
        <div className="flex items-center space-x-2 text-xs text-blue-400">
          <div className="flex space-x-1">
            <span className="inline-block w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="inline-block w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="inline-block w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span>Working...</span>
        </div>
      )}
    </div>
  );
};

