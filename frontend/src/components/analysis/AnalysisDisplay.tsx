'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { AIAnalysis } from '@/types/scan';
import { FileText, ChevronDown, ChevronUp } from 'lucide-react';

interface AnalysisDisplayProps {
  analysis: AIAnalysis;
}

export const AnalysisDisplay: React.FC<AnalysisDisplayProps> = ({ analysis }) => {
  const [showPrompt, setShowPrompt] = useState(false);

  return (
    <div className="space-y-4">
      {/* AI Prompt Section - Collapsible */}
      {analysis.prompt_text && (
        <div className="bg-[#2f2f2f] border border-[#565656] rounded-xl overflow-hidden">
          <button
            onClick={() => setShowPrompt(!showPrompt)}
            className="w-full flex items-center justify-between p-4 hover:bg-[#3a3a3a] transition-colors"
          >
            <div className="flex items-center space-x-2">
              <FileText className="h-4 w-4 text-blue-400" />
              <span className="text-sm font-medium text-white">
                AI Prompt (Input to Gemini)
              </span>
            </div>
            {showPrompt ? (
              <ChevronUp className="h-4 w-4 text-gray-400" />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-400" />
            )}
          </button>

          {showPrompt && (
            <div className="border-t border-[#565656] p-4 bg-[#1a1a1a]">
              <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono overflow-x-auto">
                {analysis.prompt_text}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* AI Analysis Response */}
      <div className="bg-[#2f2f2f] border border-[#565656] rounded-xl p-5">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-white">AI Analysis</h3>
          <div className="text-xs text-gray-400">
            {analysis.model_used} • ${analysis.cost_usd.toFixed(6)}
          </div>
        </div>

        <div className="prose prose-invert max-w-none">
          <ReactMarkdown
            components={{
              code({ inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className="bg-[#1a1a1a] px-1.5 py-0.5 rounded text-sm" {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {analysis.analysis_text}
          </ReactMarkdown>
        </div>

        <div className="mt-4 pt-4 border-t border-[#565656] text-xs text-gray-500">
          Tokens: {analysis.prompt_tokens.toLocaleString()} input + {analysis.completion_tokens.toLocaleString()} output
        </div>
      </div>
    </div>
  );
};
