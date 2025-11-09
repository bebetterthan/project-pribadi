/**
 * Real-time streaming chat component for AI Agent workflow
 * ChatGPT-style experience with typewriter effects and live terminal
 */

'use client';

import React, { useState } from 'react';
import { StreamEvent } from '@/hooks/useEventStream';
import {
  Brain,
  Zap,
  Eye,
  CheckCircle,
  XCircle,
  Loader2,
  Terminal,
  Lightbulb,
  Target
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { StreamingMessage } from '@/components/stream/TypewriterText';
import { ToolOutputCard } from './ToolOutputCard';
import { ToolExecutionCard } from './ToolExecutionCard';
import { AIDecisionCard } from './AIDecisionCard';
import { CostTracker } from './CostTracker';
import { ModelStatusIndicator } from './ModelStatusIndicator';
import { ProReasoningPanel } from './ProReasoningPanel';
import { CommandConsole } from './CommandConsole';

interface StreamingChatProps {
  messages: StreamEvent[];
  isConnected: boolean;
}

// Tool-specific icon helper
const getToolIcon = (toolName: string) => {
  const name = toolName.toLowerCase();
  if (name.includes('nmap')) return '🔍';
  if (name.includes('nuclei')) return '🎯';
  if (name.includes('whatweb')) return '🌐';
  if (name.includes('sslscan')) return '🔒';
  return '⚡';
};

const getEventIcon = (type: StreamEvent['type'], metadata?: any) => {
  switch (type) {
    case 'system':
      return <Terminal className="w-5 h-5" />;
    case 'thought':
      return <Brain className="w-5 h-5 text-purple-400" />;
    case 'plan':
      return <Lightbulb className="w-5 h-5 text-yellow-400" />;
    case 'tool':
      return <Zap className="w-5 h-5 text-blue-400 animate-pulse" />;
    case 'output':
      return <Terminal className="w-5 h-5 text-green-400" />;
    case 'analysis':
      return <Eye className="w-5 h-5 text-indigo-400" />;
    case 'decision':
      return <Target className="w-5 h-5 text-orange-400" />;
    case 'function_call':
      // Show tool-specific icon if available
      if (metadata?.tool_name) {
        return <span className="text-2xl animate-pulse">{getToolIcon(metadata.tool_name)}</span>;
      }
      return <Zap className="w-5 h-5 text-cyan-400 animate-pulse" />;
    case 'function_result':
      // Show checkmark or X based on success
      if (metadata?.status === 'error') {
        return <XCircle className="w-5 h-5 text-red-400" />;
      }
      return <CheckCircle className="w-5 h-5 text-green-400" />;
    case 'system_info':
      return <Terminal className="w-4 h-4 text-gray-500" />;
    case 'cost_report':
      return <span className="text-lg">💰</span>;
    default:
      return <Terminal className="w-5 h-5" />;
  }
};

const getEventColor = (type: StreamEvent['type']) => {
  switch (type) {
    case 'system':
      return 'border-gray-600 bg-gray-900/50';
    case 'thought':
      return 'border-purple-500/30 bg-purple-900/10';
    case 'plan':
      return 'border-yellow-500/30 bg-yellow-900/10';
    case 'tool':
      return 'border-blue-500/30 bg-blue-900/10';
    case 'output':
      return 'border-green-500/30 bg-green-900/10';
    case 'analysis':
      return 'border-indigo-500/30 bg-indigo-900/10';
    case 'decision':
      return 'border-orange-500/30 bg-orange-900/10';
    case 'function_call':
      return 'border-cyan-500/30 bg-cyan-900/10';
    case 'function_result':
      return 'border-emerald-500/30 bg-emerald-900/10';
    case 'system_info':
      return 'border-gray-700/20 bg-gray-800/5';
    case 'cost_report':
      return 'border-amber-500/30 bg-amber-900/10';
    default:
      return 'border-gray-600 bg-gray-900/50';
  }
};

const getEventLabel = (type: StreamEvent['type'], subtype?: string) => {
  if (type === 'system_info') {
    switch (subtype) {
      case 'model_selection':
        return '🤖 Model Selection';
      case 'model_switch':
        return '🔄 Model Switch';
      case 'context_handoff':
        return '📋 Context Transfer';
      default:
        return 'System Info';
    }
  }
  
  switch (type) {
    case 'system':
      return 'System';
    case 'thought':
      return 'AI Thinking';
    case 'plan':
      return 'Strategic Plan';
    case 'tool':
      return 'Tool Execution';
    case 'output':
      return 'Output';
    case 'analysis':
      return 'Analysis';
    case 'decision':
      return 'Decision';
    case 'function_call':
      return '⚡ Function Call';
    case 'function_result':
      return '✅ Function Result';
    case 'cost_report':
      return '💰 Cost Analysis';
    case 'command':
      return '📟 Command';
    case 'tool_output':
      return '📄 Live Output';
    case 'tool_start':
      return '🚀 Starting';
    case 'tool_complete':
      return '✅ Complete';
    case 'tool_error':
      return '❌ Error';
    case 'validation_start':
      return '🔍 Validating';
          case 'validation_complete':
            return '✅ Validated';
          case 'escalation':
            return '🚨 Escalation';
          case 'pro_analysis':
            return '🎯 Pro Analysis';
          case 'model_switch':
            return '🔄 Model Switch';
          default:
            return type;
        }
      };

export function StreamingChat({ messages, isConnected }: StreamingChatProps) {
  const chatEndRef = React.useRef<HTMLDivElement>(null);
  const [hoveredMessage, setHoveredMessage] = useState<number | null>(null);

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="space-y-6">
      {/* Minimalist Connection Indicator - ChatGPT style */}
      {isConnected && (
        <div className="flex items-center justify-center space-x-2 py-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-xs text-gray-600 font-medium">
            AI Agent is analyzing...
          </span>
        </div>
      )}

      {/* Clean Messages Container - ChatGPT layout */}
      <div className="space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-4">
              <Brain className="w-6 h-6 text-gray-600" />
            </div>
            <p className="text-sm text-gray-600">
              Connecting to AI Agent...
            </p>
          </div>
        ) : (
          messages.map((message, index) => {
            const isLastMessage = index === messages.length - 1;
            const shouldAnimate = isLastMessage || index >= messages.length - 3;
            
            return (
              <div
                key={index}
                onMouseEnter={() => setHoveredMessage(index)}
                onMouseLeave={() => setHoveredMessage(null)}
                className="group relative py-6 px-4 -mx-4 hover:bg-white/[0.02] transition-colors duration-200 rounded-lg"
              >
                {/* Clean Message Layout - ChatGPT style */}
                <div className="flex space-x-4">
                  {/* Icon - Pass metadata for tool-specific icons */}
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
                    {getEventIcon(message.type, message.metadata)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 space-y-3">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        {getEventLabel(message.type, message.subtype)}
                      </span>
                      {hoveredMessage === index && (
                        <span className="text-xs text-gray-600">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </span>
                      )}
                    </div>

                    {/* Message Content with Typewriter Effect */}
                    <div className="text-gray-300 text-[15px] leading-7">
                      {/* Model Status Indicator for model_switch events */}
                      {message.type === 'model_switch' ? (
                        <ModelStatusIndicator
                          currentModel={message.metadata?.to as 'flash' | 'pro' || 'transition'}
                          status={message.content}
                          transitionMessage={message.content}
                        />
                      ) : message.type === 'system_info' && message.subtype === 'model_selection' ? (
                        <ModelStatusIndicator
                          currentModel={message.metadata?.model as 'flash' | 'pro' || 'flash'}
                          status={message.content}
                          activity={message.metadata?.phase}
                        />
                      ) : message.type === 'escalation' ? (
                        <div className="bg-gradient-to-r from-amber-900/20 to-red-900/20 border border-amber-500/30 rounded-lg p-4">
                          <div className="flex items-start space-x-3">
                            <div className="flex-shrink-0">
                              <span className="text-2xl">🚨</span>
                            </div>
                            <div className="flex-1">
                              <div className="font-semibold text-amber-300 mb-2">Escalating to Pro AI</div>
                              <p className="text-amber-200/80 text-sm mb-3">{message.content}</p>
                              {message.reason && (
                                <div className="text-xs text-amber-400/70 bg-black/20 rounded p-2 border border-amber-500/20">
                                  <span className="font-semibold">Reason:</span> {message.reason}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ) : message.type === 'pro_analysis' ? (
                        <ProReasoningPanel
                          fullAnalysis={message.content}
                          streaming={isLastMessage}
                        />
                      ) : message.type === 'command' ? (
                        <CommandConsole
                          tool={message.tool || 'Tool'}
                          command={message.command || message.content}
                          explanation={message.explanation}
                          estimatedTime={message.estimated_time}
                          status="running"
                        />
                      ) : message.type === 'tool_complete' ? (
                        <CommandConsole
                          tool={message.tool || 'Tool'}
                          command={message.metadata?.command || message.content}
                          duration={message.metadata?.duration}
                          status="completed"
                        />
                      ) : message.type === 'thought' || message.type === 'analysis' ? (
                        message.metadata?.model === 'pro' ? (
                          <ProReasoningPanel
                            fullAnalysis={message.content}
                            streaming={shouldAnimate}
                          />
                        ) : (
                          <StreamingMessage 
                            content={message.content}
                            type={message.type}
                            animate={shouldAnimate}
                            speed={30}
                          />
                        )
                      ) : message.type === 'tool' ? (
                        <div className="inline-flex items-center px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20">
                          <Zap className="w-3 h-3 mr-2 text-blue-400" />
                          <span className="text-sm text-blue-300 font-mono">{message.content}</span>
                        </div>
                      ) : message.type === 'function_call' ? (
                        <ToolExecutionCard
                          toolName={message.metadata?.tool_name || message.metadata?.function || 'Tool'}
                          content={message.content}
                          metadata={message.metadata}
                        />
                      ) : message.type === 'function_result' ? (
                        <div className="bg-gradient-to-r from-emerald-500/10 to-green-500/10 border border-emerald-500/20 rounded-lg p-4">
                          <div className="flex items-start space-x-3">
                            <CheckCircle className="w-5 h-5 text-emerald-400 mt-1" />
                            <div className="flex-1">
                              <ReactMarkdown 
                                className="prose prose-invert prose-sm max-w-none text-emerald-100"
                                components={{
                                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                  strong: ({ children }) => <strong className="text-emerald-200 font-semibold">{children}</strong>,
                                }}
                              >
                                {message.content}
                              </ReactMarkdown>
                            </div>
                          </div>
                        </div>
                      ) : message.type === 'plan' ? (
                        <div className="bg-gradient-to-r from-yellow-500/5 to-orange-500/5 border-l-2 border-yellow-500/50 pl-4 py-2">
                          <ReactMarkdown className="prose prose-invert prose-sm max-w-none">
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      ) : message.type === 'decision' ? (
                        <AIDecisionCard
                          content={message.content}
                          metadata={message.metadata}
                        />
                      ) : message.type === 'cost_report' ? (
                        <CostTracker metadata={message.metadata} />
                      ) : message.type === 'output' ? (
                        <ToolOutputCard 
                          content={message.content}
                          metadata={message.metadata}
                        />
                      ) : (
                        <ReactMarkdown
                          className="prose prose-invert prose-sm max-w-none"
                          components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                            strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
                            ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2">{children}</ul>,
                            li: ({ children }) => <li className="text-gray-300">{children}</li>,
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      )}
                    </div>

                    {/* Clean Metadata Pills */}
                    {message.metadata && Object.keys(message.metadata).length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {/* Phase Indicator - NEW! */}
                        {message.metadata.phase && (
                          <span className={`inline-flex items-center text-xs px-3 py-1 rounded-full font-medium border ${
                            message.metadata.phase === 'flash_reconnaissance'
                              ? 'bg-blue-500/10 text-blue-300 border-blue-500/30'
                              : message.metadata.phase === 'pro_analysis'
                              ? 'bg-purple-500/10 text-purple-300 border-purple-500/30'
                              : message.metadata.phase === 'transition'
                              ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                              : message.metadata.phase === 'evaluation'
                              ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                              : 'bg-gray-500/10 text-gray-300 border-gray-500/30'
                          }`}>
                            {message.metadata.phase === 'flash_reconnaissance'
                              ? '⚡ Phase 1: Flash Reconnaissance'
                              : message.metadata.phase === 'pro_analysis'
                              ? '🎓 Phase 2: Pro Deep Analysis'
                              : message.metadata.phase === 'transition'
                              ? '🔄 Transitioning Models'
                              : message.metadata.phase === 'evaluation'
                              ? '🔍 Evaluating Complexity'
                              : message.metadata.phase}
                          </span>
                        )}
                        {/* Model Badge - NEW! */}
                        {message.metadata.model && (
                          <span className={`inline-flex items-center text-xs px-3 py-1 rounded-full font-medium border ${
                            message.metadata.model === 'flash'
                              ? 'bg-blue-600/20 text-blue-200 border-blue-400/40'
                              : 'bg-purple-600/20 text-purple-200 border-purple-400/40'
                          }`}>
                            {message.metadata.model === 'flash' ? '⚡ Flash Model' : '🎓 Pro Model'}
                          </span>
                        )}
                        {message.metadata.tools && (
                          <span className="inline-flex items-center text-xs px-2.5 py-1 bg-white/5 text-gray-400 rounded-full border border-white/10">
                            {Array.isArray(message.metadata.tools)
                              ? message.metadata.tools.join(', ')
                              : message.metadata.tools}
                          </span>
                        )}
                        {message.metadata.confidence && (
                          <span className="inline-flex items-center text-xs px-2.5 py-1 bg-white/5 text-gray-400 rounded-full border border-white/10">
                            {(message.metadata.confidence * 100).toFixed(0)}% confidence
                          </span>
                        )}
                        {message.metadata.iteration && (
                          <span className="inline-flex items-center text-xs px-2.5 py-1 bg-white/5 text-gray-400 rounded-full border border-white/10">
                            Step {message.metadata.iteration}/{message.metadata.max}
                          </span>
                        )}
                        {/* Context Serialization Progress - NEW! */}
                        {message.metadata.tokens && (
                          <span className="inline-flex items-center text-xs px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20">
                            📄 {Math.floor(message.metadata.tokens / 1000)}K tokens
                          </span>
                        )}
                        {/* Pro Usage Indicator - NEW! */}
                        {message.metadata.pro_used !== undefined && (
                          <span className={`inline-flex items-center text-xs px-2.5 py-1 rounded-full border ${
                            message.metadata.pro_used
                              ? 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                              : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                          }`}>
                            {message.metadata.pro_used ? '🎓 Pro Analysis Used' : '⚡ Flash Only'}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}

        {/* Auto-scroll anchor */}
        <div ref={chatEndRef} />
      </div>

      {/* Custom Scrollbar Styles */}
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgb(17, 24, 39);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgb(55, 65, 81);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgb(75, 85, 99);
        }
      `}</style>
    </div>
  );
}
