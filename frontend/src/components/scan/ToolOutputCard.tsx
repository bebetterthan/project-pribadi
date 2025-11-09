/**
 * ToolOutputCard - Rich display for tool execution outputs
 * Implements collapsible, searchable, copyable tool results
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Copy, Download, Search, CheckCircle, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface ToolOutputCardProps {
  content: string;
  metadata?: {
    tool?: string;
    status?: string;
    execution_time?: number;
    elapsed?: number;
    error?: boolean;
    findings?: number;  // NEW: Total findings count
    interesting?: number;  // NEW: Interesting findings count
  };
}

export function ToolOutputCard({ content, metadata }: ToolOutputCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);
  
  const toolName = metadata?.tool || 'Tool';
  const status = metadata?.status || 'unknown';
  const isError = metadata?.error || false;
  const executionTime = metadata?.execution_time || metadata?.elapsed;

  // Extract summary (first few lines) and full content
  const lines = content.split('\n');
  const summaryLines = lines.slice(0, 5);
  const hasMore = lines.length > 5;

  // Detect if content has structured data
  const hasStructuredData = content.includes('```') || content.includes('**');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${toolName}-output-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`
      rounded-lg border transition-all duration-200
      ${isError 
        ? 'bg-red-500/5 border-red-500/20' 
        : status === 'starting' 
          ? 'bg-blue-500/5 border-blue-500/20'
          : 'bg-emerald-500/5 border-emerald-500/20'
      }
    `}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/5">
        <div className="flex items-center space-x-3">
          {isError ? (
            <AlertCircle className="w-5 h-5 text-red-400" />
          ) : status === 'starting' ? (
            <div className="w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
          ) : (
            <CheckCircle className="w-5 h-5 text-emerald-400" />
          )}
          <div>
            <div className="text-sm font-medium text-gray-200">
              {toolName}
              {executionTime && (
                <span className="text-xs text-gray-500 ml-2">
                  ({executionTime}s)
                </span>
              )}
            </div>
            <div className="flex items-center space-x-3">
              <div className="text-xs text-gray-500 capitalize">
                {status}
              </div>
              {/* NEW: Display findings count */}
              {metadata?.findings !== undefined && (
                <div className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  metadata.findings > 0 
                    ? 'bg-emerald-500/20 text-emerald-300' 
                    : 'bg-gray-500/20 text-gray-400'
                }`}>
                  {metadata.findings} finding{metadata.findings !== 1 ? 's' : ''}
                  {metadata.interesting && metadata.interesting > 0 && (
                    <span className="ml-1 text-amber-300">
                      ({metadata.interesting} interesting)
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="p-2 hover:bg-white/5 rounded-lg transition-colors"
            title="Copy to clipboard"
          >
            {copied ? (
              <CheckCircle className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4 text-gray-400" />
            )}
          </button>
          <button
            onClick={handleDownload}
            className="p-2 hover:bg-white/5 rounded-lg transition-colors"
            title="Download output"
          >
            <Download className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {hasStructuredData ? (
          // Render markdown for structured content
          <ReactMarkdown
            className="prose prose-invert prose-sm max-w-none"
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0 text-gray-300">{children}</p>,
              strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
              ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2">{children}</ul>,
              li: ({ children }) => <li className="text-gray-300">{children}</li>,
              code: ({ inline, children, ...props }: any) => {
                if (inline) {
                  return <code className="bg-black/30 px-1.5 py-0.5 rounded text-sm font-mono text-cyan-300" {...props}>{children}</code>;
                }
                return (
                  <pre className="bg-black/30 p-3 rounded-lg overflow-x-auto my-2">
                    <code className="text-sm font-mono text-gray-300" {...props}>{children}</code>
                  </pre>
                );
              },
            }}
          >
            {isExpanded ? content : summaryLines.join('\n')}
          </ReactMarkdown>
        ) : (
          // Plain text output
          <pre className="text-sm font-mono text-gray-300 whitespace-pre-wrap overflow-x-auto">
            {isExpanded ? content : summaryLines.join('\n')}
          </pre>
        )}

        {/* Expand/Collapse Button */}
        {hasMore && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-2 mt-3 text-sm text-blue-400 hover:text-blue-300 transition-colors"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="w-4 h-4" />
                <span>Show less</span>
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                <span>Show full output ({lines.length} lines)</span>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

