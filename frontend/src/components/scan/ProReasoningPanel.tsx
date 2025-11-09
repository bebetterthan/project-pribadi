'use client';

import React, { useState, useEffect } from 'react';
import { Brain, ChevronDown, ChevronUp, Target, Shield, AlertTriangle, CheckCircle2, Lightbulb, TrendingUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface ReasoningSection {
  title: string;
  content: string;
  icon?: 'target' | 'shield' | 'alert' | 'check' | 'lightbulb';
  expanded?: boolean;
}

interface ProReasoningPanelProps {
  strategy?: string;
  sections?: ReasoningSection[];
  fullAnalysis?: string;
  streaming?: boolean;
}

export const ProReasoningPanel: React.FC<ProReasoningPanelProps> = ({
  strategy,
  sections = [],
  fullAnalysis,
  streaming = false
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<number>>(
    new Set(sections.map((_, idx) => idx).filter(idx => sections[idx].expanded))
  );
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Typewriter effect for streaming content
  useEffect(() => {
    if (streaming && fullAnalysis) {
      setIsTyping(true);
      let currentIndex = 0;
      const interval = setInterval(() => {
        if (currentIndex <= fullAnalysis.length) {
          setDisplayedText(fullAnalysis.substring(0, currentIndex));
          currentIndex += 2; // Speed: 2 characters at a time
        } else {
          setIsTyping(false);
          clearInterval(interval);
        }
      }, 20); // 20ms per update = ~50 chars/second

      return () => clearInterval(interval);
    } else if (fullAnalysis) {
      setDisplayedText(fullAnalysis);
    }
  }, [fullAnalysis, streaming]);

  const toggleSection = (index: number) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSections(newExpanded);
  };

  const getIcon = (iconType?: string) => {
    switch (iconType) {
      case 'target':
        return <Target className="h-4 w-4 text-purple-400" />;
      case 'shield':
        return <Shield className="h-4 w-4 text-purple-400" />;
      case 'alert':
        return <AlertTriangle className="h-4 w-4 text-purple-400" />;
      case 'check':
        return <CheckCircle2 className="h-4 w-4 text-purple-400" />;
      case 'lightbulb':
        return <Lightbulb className="h-4 w-4 text-purple-400" />;
      default:
        return <TrendingUp className="h-4 w-4 text-purple-400" />;
    }
  };

  return (
    <div className="relative overflow-hidden rounded-xl border border-purple-500/30 bg-gradient-to-br from-purple-900/10 via-purple-800/5 to-pink-900/10">
      {/* Subtle animated background */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(168,85,247,0.4),transparent_50%)] animate-pulse" style={{ animationDuration: '4s' }} />
      </div>

      <div className="relative">
        {/* Header */}
        <div className="px-6 py-4 border-b border-purple-500/20 bg-gradient-to-r from-purple-900/20 to-transparent">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="absolute inset-0 bg-purple-500 rounded-lg blur-sm opacity-30" />
              <div className="relative bg-purple-500/20 p-2 rounded-lg border border-purple-400/30">
                <Brain className="h-5 w-5 text-purple-300" strokeWidth={2} />
              </div>
            </div>
            <div>
              <h3 className="text-lg font-bold text-purple-200 font-serif">
                AI Strategic Reasoning
              </h3>
              <p className="text-xs text-purple-400/70">Pro 2.5 Deep Analysis</p>
            </div>
            {streaming && isTyping && (
              <div className="ml-auto flex items-center space-x-2 text-purple-400">
                <div className="flex space-x-1">
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="text-xs font-medium">Analyzing...</span>
              </div>
            )}
          </div>
        </div>

        {/* Main Strategy (if provided) */}
        {strategy && (
          <div className="px-6 py-5 border-b border-purple-500/10 bg-black/10">
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <p className="mb-3 last:mb-0 text-gray-300 leading-relaxed font-serif text-base">
                      {children}
                    </p>
                  ),
                  strong: ({ children }) => (
                    <strong className="text-purple-200 font-semibold">{children}</strong>
                  ),
                  ul: ({ children }) => (
                    <ul className="space-y-2 my-3">{children}</ul>
                  ),
                  li: ({ children }) => (
                    <li className="text-gray-300 flex items-start space-x-2">
                      <span className="text-purple-400 mt-1">•</span>
                      <span className="flex-1">{children}</span>
                    </li>
                  ),
                }}
              >
                {strategy}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {/* Expandable Sections */}
        {sections.length > 0 && (
          <div className="divide-y divide-purple-500/10">
            {sections.map((section, index) => {
              const isExpanded = expandedSections.has(index);
              
              return (
                <div key={index} className="transition-colors hover:bg-purple-500/5">
                  {/* Section Header */}
                  <button
                    onClick={() => toggleSection(index)}
                    className="w-full px-6 py-4 flex items-center justify-between group"
                  >
                    <div className="flex items-center space-x-3">
                      {getIcon(section.icon)}
                      <span className="text-sm font-semibold text-purple-200 group-hover:text-purple-100 transition-colors">
                        {section.title}
                      </span>
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="h-5 w-5 text-purple-400 group-hover:text-purple-300 transition-colors" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-purple-400 group-hover:text-purple-300 transition-colors" />
                    )}
                  </button>

                  {/* Section Content */}
                  {isExpanded && (
                    <div className="px-6 pb-4 animate-in slide-in-from-top-2 duration-300">
                      <div className="pl-8 pr-4 py-3 bg-black/20 rounded-lg border border-purple-500/10">
                        <div className="prose prose-invert prose-sm max-w-none">
                          <ReactMarkdown
                            components={{
                              p: ({ children }) => (
                                <p className="mb-2 last:mb-0 text-gray-300 leading-relaxed text-sm">
                                  {children}
                                </p>
                              ),
                              strong: ({ children }) => (
                                <strong className="text-purple-200 font-semibold">{children}</strong>
                              ),
                              ul: ({ children }) => (
                                <ul className="space-y-1.5 my-2">{children}</ul>
                              ),
                              li: ({ children }) => (
                                <li className="text-gray-300 text-sm flex items-start space-x-2">
                                  <span className="text-purple-400 mt-0.5 text-xs">▸</span>
                                  <span className="flex-1">{children}</span>
                                </li>
                              ),
                            }}
                          >
                            {section.content}
                          </ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Full Analysis (streaming or static) */}
        {fullAnalysis && (
          <div className="px-6 py-5 bg-black/10">
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                components={{
                  p: ({ children }) => (
                    <p className="mb-3 last:mb-0 text-gray-300 leading-relaxed font-serif">
                      {children}
                      {isTyping && <span className="inline-block w-2 h-4 ml-1 bg-purple-400 animate-pulse" />}
                    </p>
                  ),
                  strong: ({ children }) => (
                    <strong className="text-purple-200 font-semibold">{children}</strong>
                  ),
                  h1: ({ children }) => (
                    <h1 className="text-xl font-bold text-purple-100 mb-3 mt-4 first:mt-0">{children}</h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-lg font-semibold text-purple-200 mb-2 mt-3">{children}</h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-base font-semibold text-purple-300 mb-2 mt-2">{children}</h3>
                  ),
                  ul: ({ children }) => (
                    <ul className="space-y-2 my-3">{children}</ul>
                  ),
                  li: ({ children }) => (
                    <li className="text-gray-300 flex items-start space-x-2">
                      <span className="text-purple-400 mt-1">•</span>
                      <span className="flex-1">{children}</span>
                    </li>
                  ),
                  code: ({ children, ...props }) => {
                    // @ts-ignore
                    const isInline = !props.className;
                    if (isInline) {
                      return (
                        <code className="px-1.5 py-0.5 bg-purple-900/30 text-purple-200 rounded text-sm font-mono border border-purple-500/20">
                          {children}
                        </code>
                      );
                    }
                    return (
                      <code className="block p-3 bg-black/40 text-gray-300 rounded-lg text-sm font-mono overflow-x-auto border border-purple-500/20" {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {displayedText}
              </ReactMarkdown>
            </div>
          </div>
        )}

        {/* Footer indicator */}
        <div className="px-6 py-3 border-t border-purple-500/20 bg-gradient-to-r from-transparent to-purple-900/10">
          <div className="flex items-center justify-between text-xs text-purple-400/60">
            <span className="flex items-center space-x-1">
              <Brain className="h-3 w-3" />
              <span>Generated by Pro AI 2.5</span>
            </span>
            <span className="flex items-center space-x-1">
              <span>Premium Strategic Analysis</span>
              <CheckCircle2 className="h-3 w-3" />
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

