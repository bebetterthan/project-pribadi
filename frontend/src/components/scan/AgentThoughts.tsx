'use client';

import { AgentThought } from '@/types/scan';
import { useState } from 'react';

interface AgentThoughtsProps {
  thoughts: AgentThought[];
}

const stateEmojis: Record<string, string> = {
  planning: '🎯',
  executing: '⚙️',
  analyzing: '🔍',
  refining: '🔄',
  complete: '✅',
};

const stateColors: Record<string, string> = {
  planning: 'border-blue-500/50 bg-blue-500/10',
  executing: 'border-yellow-500/50 bg-yellow-500/10',
  analyzing: 'border-purple-500/50 bg-purple-500/10',
  refining: 'border-orange-500/50 bg-orange-500/10',
  complete: 'border-green-500/50 bg-green-500/10',
};

export default function AgentThoughts({ thoughts }: AgentThoughtsProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set([1])); // First step expanded by default

  const toggleStep = (step: number) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(step)) {
      newExpanded.delete(step);
    } else {
      newExpanded.add(step);
    }
    setExpandedSteps(newExpanded);
  };

  const expandAll = () => {
    setExpandedSteps(new Set(thoughts.map(t => t.step)));
  };

  const collapseAll = () => {
    setExpandedSteps(new Set());
  };

  if (!thoughts || thoughts.length === 0) {
    return null;
  }

  return (
    <div className="bg-[#2f2f2f] border border-[#565656] rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <h3 className="text-xl font-semibold text-white">AI Agent Thought Process</h3>
          <span className="text-sm text-gray-400">({thoughts.length} steps)</span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={expandAll}
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            Expand All
          </button>
          <span className="text-gray-600">|</span>
          <button
            onClick={collapseAll}
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            Collapse All
          </button>
        </div>
      </div>

      <p className="text-sm text-gray-400 mb-6">
        💡 See how the AI reasoned through your objective step-by-step, adapting its strategy based on findings.
      </p>

      {/* Timeline */}
      <div className="space-y-3">
        {thoughts.map((thought, index) => {
          const isExpanded = expandedSteps.has(thought.step);
          const isLast = index === thoughts.length - 1;

          return (
            <div key={thought.step} className="relative">
              {/* Timeline connector */}
              {!isLast && (
                <div className="absolute left-[19px] top-10 w-0.5 h-full bg-gradient-to-b from-blue-500/30 to-transparent" />
              )}

              {/* Step card */}
              <div
                className={`border rounded-lg transition-all ${
                  stateColors[thought.state] || 'border-gray-600 bg-gray-800/50'
                }`}
              >
                {/* Step header - clickable */}
                <button
                  onClick={() => toggleStep(thought.step)}
                  className="w-full flex items-center gap-3 p-4 text-left hover:bg-white/5 transition-colors rounded-t-lg"
                >
                  {/* Step number badge */}
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold shadow-lg">
                    {thought.step}
                  </div>

                  {/* State badge */}
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{stateEmojis[thought.state]}</span>
                    <span className="text-sm font-medium text-gray-300 capitalize">
                      {thought.state}
                    </span>
                  </div>

                  {/* Expand/collapse indicator */}
                  <div className="ml-auto text-gray-500">
                    {isExpanded ? '▼' : '▶'}
                  </div>
                </button>

                {/* Expanded content */}
                {isExpanded && (
                  <div className="px-4 pb-4 space-y-3 border-t border-white/10">
                    {/* Thought */}
                    <div>
                      <div className="flex items-center gap-2 mb-1 mt-3">
                        <span className="text-sm font-semibold text-blue-400">💭 Thought</span>
                      </div>
                      <p className="text-sm text-gray-300 leading-relaxed pl-6">
                        {thought.thought}
                      </p>
                    </div>

                    {/* Action */}
                    {thought.action && (
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-semibold text-green-400">⚡ Action</span>
                        </div>
                        <p className="text-sm text-gray-300 leading-relaxed pl-6">
                          {thought.action}
                        </p>
                      </div>
                    )}

                    {/* Observation */}
                    {thought.observation && (
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-semibold text-purple-400">👁️ Observation</span>
                        </div>
                        <p className="text-sm text-gray-300 leading-relaxed pl-6 whitespace-pre-wrap">
                          {thought.observation}
                        </p>
                      </div>
                    )}

                    {/* Timestamp */}
                    <div className="text-xs text-gray-500 pl-6 pt-2">
                      {new Date(thought.timestamp).toLocaleString()}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-6 p-4 bg-gradient-to-r from-blue-900/20 to-purple-900/20 rounded-lg border border-blue-500/30">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lg">🎯</span>
          <span className="text-sm font-semibold text-blue-300">Agent Summary</span>
        </div>
        <p className="text-sm text-gray-300">
          The AI agent completed {thoughts.length} reasoning steps, adapting its strategy based on
          real-time observations. This transparent thought process shows how the agent interpreted
          your objective and made intelligent decisions about which tools to use and when.
        </p>
      </div>
    </div>
  );
}
