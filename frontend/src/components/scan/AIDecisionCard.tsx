/**
 * AIDecisionCard - Displays AI reasoning and decision points
 * Shows WHY the AI made specific choices (transparency feature)
 */

import React, { useState } from 'react';
import { Brain, ChevronDown, ChevronUp, Lightbulb, Target, AlertTriangle, CheckCircle2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface AIDecisionCardProps {
  content: string;
  metadata?: {
    reasoning?: string;
    alternatives?: string[];
    confidence?: number;
    risk_level?: 'low' | 'medium' | 'high';
    decision_type?: 'strategic' | 'tactical' | 'safety';
  };
}

export function AIDecisionCard({ content, metadata }: AIDecisionCardProps) {
  const [showReasoning, setShowReasoning] = useState(false);
  
  const hasReasoning = metadata?.reasoning || metadata?.alternatives;
  const confidence = metadata?.confidence || 0;
  const riskLevel = metadata?.risk_level || 'low';
  const decisionType = metadata?.decision_type || 'tactical';

  // Color scheme based on decision type
  const typeColors = {
    strategic: {
      border: 'border-purple-500/30',
      bg: 'bg-purple-500/5',
      text: 'text-purple-400',
      icon: 'text-purple-400',
    },
    tactical: {
      border: 'border-blue-500/30',
      bg: 'bg-blue-500/5',
      text: 'text-blue-400',
      icon: 'text-blue-400',
    },
    safety: {
      border: 'border-amber-500/30',
      bg: 'bg-amber-500/5',
      text: 'text-amber-400',
      icon: 'text-amber-400',
    },
  };

  const colors = typeColors[decisionType];

  // Risk indicator
  const getRiskIcon = () => {
    switch (riskLevel) {
      case 'low':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'medium':
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      case 'high':
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
      default:
        return null;
    }
  };

  return (
    <div className={`rounded-lg border ${colors.border} ${colors.bg} overflow-hidden`}>
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start space-x-3">
          <div className="mt-0.5">
            <Target className={`w-5 h-5 ${colors.icon}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h4 className={`text-sm font-semibold ${colors.text}`}>
                AI Decision Point
              </h4>
              <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-gray-400 capitalize">
                {decisionType}
              </span>
              {getRiskIcon()}
            </div>
            
            {/* Confidence Bar */}
            {confidence > 0 && (
              <div className="mt-2">
                <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                  <span>Confidence</span>
                  <span>{Math.round(confidence * 100)}%</span>
                </div>
                <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${colors.bg} bg-gradient-to-r from-${colors.text.replace('text-', '')} to-${colors.text.replace('text-', '')}/50 transition-all duration-500`}
                    style={{ width: `${confidence * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Decision Content */}
      <div className="p-4">
        <ReactMarkdown
          className="prose prose-invert prose-sm max-w-none"
          components={{
            p: ({ children }) => <p className="mb-2 last:mb-0 text-gray-300 leading-relaxed">{children}</p>,
            strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
          }}
        >
          {content}
        </ReactMarkdown>

        {/* Expandable Reasoning Section */}
        {hasReasoning && (
          <div className="mt-4">
            <button
              onClick={() => setShowReasoning(!showReasoning)}
              className="flex items-center space-x-2 text-sm text-gray-400 hover:text-gray-300 transition-colors"
            >
              {showReasoning ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  <span>Hide reasoning</span>
                </>
              ) : (
                <>
                  <Lightbulb className="w-4 h-4" />
                  <span>Show why this decision was made</span>
                </>
              )}
            </button>

            {showReasoning && (
              <div className="mt-3 space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                {/* AI Reasoning */}
                {metadata?.reasoning && (
                  <div className="bg-black/20 rounded-lg p-4 border border-white/5">
                    <div className="flex items-start space-x-2 mb-2">
                      <Brain className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                      <h5 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                        Reasoning Process
                      </h5>
                    </div>
                    <p className="text-sm text-gray-300 leading-relaxed">
                      {metadata.reasoning}
                    </p>
                  </div>
                )}

                {/* Alternatives Considered */}
                {metadata?.alternatives && metadata.alternatives.length > 0 && (
                  <div className="bg-black/20 rounded-lg p-4 border border-white/5">
                    <h5 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                      Alternatives Considered
                    </h5>
                    <ul className="space-y-1">
                      {metadata.alternatives.map((alt, idx) => (
                        <li key={idx} className="text-sm text-gray-400 flex items-start space-x-2">
                          <span className="text-gray-600 mt-0.5">•</span>
                          <span>{alt}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

