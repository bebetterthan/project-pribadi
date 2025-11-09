'use client';

import React, { useState } from 'react';
import { Terminal, Copy, Check, Info, ChevronDown, ChevronUp, Clock, Zap } from 'lucide-react';

interface CommandFlag {
  flag: string;
  description: string;
}

interface CommandConsoleProps {
  tool: string;
  command: string;
  explanation?: string;
  estimatedTime?: string;
  duration?: number;
  flags?: CommandFlag[];
  status?: 'running' | 'completed' | 'failed';
}

export const CommandConsole: React.FC<CommandConsoleProps> = ({
  tool,
  command,
  explanation,
  estimatedTime,
  duration,
  flags = [],
  status = 'running'
}) => {
  const [copied, setCopied] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [showFlags, setShowFlags] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Parse command to highlight flags
  const renderCommand = () => {
    const parts = command.split(' ');
    return parts.map((part, index) => {
      if (part.startsWith('-')) {
        return (
          <span key={index} className="text-yellow-400">
            {part}{' '}
          </span>
        );
      } else if (index === 0) {
        return (
          <span key={index} className="text-green-400 font-semibold">
            {part}{' '}
          </span>
        );
      } else {
        return (
          <span key={index} className="text-cyan-300">
            {part}{' '}
          </span>
        );
      }
    });
  };

  // Extract flags from command if not provided
  const extractedFlags = flags.length > 0 ? flags : command
    .split(' ')
    .filter(part => part.startsWith('-'))
    .map(flag => ({ flag, description: 'Command flag' }));

  return (
    <div className="rounded-lg border border-gray-700 bg-[#0d1117] overflow-hidden shadow-lg">
      {/* Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-[#161b22] to-[#0d1117] border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Terminal className="h-5 w-5 text-green-400" />
              {status === 'running' && (
                <span className="absolute -top-1 -right-1 flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
              )}
            </div>
            <div>
              <h4 className="text-sm font-semibold text-green-400 flex items-center space-x-2">
                <span>{tool.toUpperCase()}</span>
                {status === 'running' && (
                  <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-300 rounded border border-green-500/30">
                    Executing
                  </span>
                )}
                {status === 'completed' && (
                  <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-300 rounded border border-blue-500/30">
                    Completed
                  </span>
                )}
                {status === 'failed' && (
                  <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-300 rounded border border-red-500/30">
                    Failed
                  </span>
                )}
              </h4>
              <p className="text-xs text-gray-500">Command Execution</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Duration */}
            {duration !== undefined && (
              <div className="flex items-center space-x-1 text-xs text-gray-400">
                <Clock className="h-3.5 w-3.5" />
                <span>{duration.toFixed(1)}s</span>
              </div>
            )}
            
            {/* Estimated Time */}
            {estimatedTime && !duration && (
              <div className="flex items-center space-x-1 text-xs text-yellow-400/70">
                <Zap className="h-3.5 w-3.5" />
                <span>~{estimatedTime}</span>
              </div>
            )}
            
            {/* Copy Button */}
            <button
              onClick={handleCopy}
              className="p-1.5 hover:bg-gray-700/50 rounded transition-colors group"
              title="Copy command"
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-400" />
              ) : (
                <Copy className="h-4 w-4 text-gray-500 group-hover:text-gray-300" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Explanation (collapsible) */}
      {explanation && (
        <div className="border-b border-gray-700">
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="w-full px-4 py-2 flex items-center justify-between hover:bg-gray-800/30 transition-colors group"
          >
            <div className="flex items-center space-x-2 text-xs text-gray-400 group-hover:text-gray-300">
              <Info className="h-3.5 w-3.5" />
              <span>What does this command do?</span>
            </div>
            {showExplanation ? (
              <ChevronUp className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-500" />
            )}
          </button>
          
          {showExplanation && (
            <div className="px-4 py-3 bg-blue-500/5 border-t border-blue-500/10 animate-in slide-in-from-top-2 duration-200">
              <p className="text-sm text-gray-300 leading-relaxed">
                {explanation}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Command Display */}
      <div className="relative">
        <div className="px-4 py-4 bg-black/40 font-mono text-sm overflow-x-auto">
          <div className="flex items-start space-x-2">
            <span className="text-green-400 select-none mt-0.5">$</span>
            <div className="flex-1 text-gray-100 whitespace-pre-wrap break-all">
              {renderCommand()}
            </div>
          </div>
          
          {/* Blinking cursor for running state */}
          {status === 'running' && (
            <div className="mt-2 flex items-center">
              <span className="inline-block w-2 h-4 bg-green-400 animate-pulse" />
            </div>
          )}
        </div>

        {/* Terminal scanlines effect */}
        <div className="absolute inset-0 pointer-events-none opacity-5">
          <div className="h-full w-full" style={{
            backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.03) 2px, rgba(255,255,255,0.03) 4px)'
          }} />
        </div>
      </div>

      {/* Flag Explanations (collapsible) */}
      {extractedFlags.length > 0 && (
        <div className="border-t border-gray-700">
          <button
            onClick={() => setShowFlags(!showFlags)}
            className="w-full px-4 py-2 flex items-center justify-between hover:bg-gray-800/30 transition-colors group"
          >
            <div className="flex items-center space-x-2 text-xs text-gray-400 group-hover:text-gray-300">
              <Info className="h-3.5 w-3.5" />
              <span>Command flags explained ({extractedFlags.length})</span>
            </div>
            {showFlags ? (
              <ChevronUp className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-500" />
            )}
          </button>
          
          {showFlags && (
            <div className="px-4 py-3 bg-black/20 border-t border-gray-700 animate-in slide-in-from-top-2 duration-200">
              <div className="space-y-2">
                {extractedFlags.map((item, index) => (
                  <div key={index} className="flex items-start space-x-3 text-xs">
                    <code className="px-2 py-0.5 bg-yellow-400/10 text-yellow-300 rounded font-mono border border-yellow-500/20 whitespace-nowrap">
                      {item.flag}
                    </code>
                    <span className="text-gray-400 flex-1 pt-0.5">
                      {item.description}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Footer hint */}
      <div className="px-4 py-2 bg-[#161b22] border-t border-gray-700">
        <p className="text-xs text-gray-600 text-center">
          This is the actual command executed by Agent-P
        </p>
      </div>
    </div>
  );
};

