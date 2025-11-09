/**
 * ProgressTimeline - Visual timeline of scan workflow
 * Shows what's happening, what's completed, and what's next
 */

import React from 'react';
import { CheckCircle2, Circle, Clock, Loader2 } from 'lucide-react';

interface TimelineStep {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  timestamp?: string;
  duration?: number;
}

interface ProgressTimelineProps {
  steps: TimelineStep[];
  currentStep?: string;
}

export function ProgressTimeline({ steps, currentStep }: ProgressTimelineProps) {
  if (steps.length === 0) return null;

  const getStepIcon = (status: TimelineStep['status'], isLast: boolean) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-400" />;
      case 'in_progress':
        return <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />;
      case 'error':
        return <div className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
          <span className="text-white text-xs">✕</span>
        </div>;
      case 'pending':
        return <Circle className="w-5 h-5 text-gray-600" />;
      default:
        return <Circle className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStepColor = (status: TimelineStep['status']) => {
    switch (status) {
      case 'completed':
        return 'border-green-500/30 bg-green-500/5';
      case 'in_progress':
        return 'border-blue-500/30 bg-blue-500/5';
      case 'error':
        return 'border-red-500/30 bg-red-500/5';
      default:
        return 'border-gray-700/30 bg-gray-800/5';
    }
  };

  return (
    <div className="bg-[#141414] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center space-x-2 mb-4">
        <Clock className="w-4 h-4 text-gray-500" />
        <h3 className="text-sm font-semibold text-gray-300">Workflow Timeline</h3>
      </div>

      <div className="relative">
        {/* Vertical line connecting steps */}
        <div className="absolute left-[10px] top-[30px] bottom-[30px] w-[2px] bg-gradient-to-b from-blue-500/30 via-purple-500/30 to-gray-700/30" />

        {/* Steps */}
        <div className="space-y-4">
          {steps.map((step, index) => {
            const isLast = index === steps.length - 1;
            const isCurrent = step.id === currentStep || step.status === 'in_progress';

            return (
              <div
                key={step.id}
                className={`relative pl-10 pb-4 ${isCurrent ? 'animate-in fade-in slide-in-from-left-2 duration-300' : ''}`}
              >
                {/* Icon */}
                <div className={`absolute left-0 top-0 z-10 rounded-full ${
                  isCurrent ? 'ring-4 ring-blue-500/20' : ''
                }`}>
                  {getStepIcon(step.status, isLast)}
                </div>

                {/* Content */}
                <div className={`rounded-lg border ${getStepColor(step.status)} p-3 transition-all duration-200 ${
                  isCurrent ? 'shadow-lg' : ''
                }`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className={`text-sm font-medium ${
                        step.status === 'completed' ? 'text-green-300' :
                        step.status === 'in_progress' ? 'text-blue-300' :
                        step.status === 'error' ? 'text-red-300' :
                        'text-gray-400'
                      }`}>
                        {step.title}
                      </h4>
                      {step.description && (
                        <p className="text-xs text-gray-500 mt-1">
                          {step.description}
                        </p>
                      )}
                    </div>

                    {/* Timestamp or duration */}
                    <div className="text-xs text-gray-600 ml-3 flex-shrink-0">
                      {step.duration ? (
                        <span>{step.duration}s</span>
                      ) : step.timestamp ? (
                        <span>{new Date(step.timestamp).toLocaleTimeString()}</span>
                      ) : null}
                    </div>
                  </div>

                  {/* Progress bar for in-progress items */}
                  {step.status === 'in_progress' && (
                    <div className="mt-2 h-1 bg-gray-800 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 animate-pulse" style={{ width: '60%' }} />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

