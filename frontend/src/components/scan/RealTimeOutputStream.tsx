'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Pause, Play, Download, ChevronDown, ChevronUp, Maximize2, Minimize2 } from 'lucide-react';

interface OutputLine {
  line_number: number;
  content: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'summary';
  timestamp: string;
}

interface RealTimeOutputStreamProps {
  tool: string;
  lines: OutputLine[];
  isStreaming: boolean;
  maxHeight?: string;
}

export const RealTimeOutputStream: React.FC<RealTimeOutputStreamProps> = ({
  tool,
  lines,
  isStreaming,
  maxHeight = '400px'
}) => {
  const [autoScroll, setAutoScroll] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const outputRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new lines arrive (if enabled)
  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [lines, autoScroll]);

  // Detect manual scroll - disable auto-scroll if user scrolls up
  const handleScroll = () => {
    if (!outputRef.current) return;
    
    const { scrollTop, scrollHeight, clientHeight } = outputRef.current;
    const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 50;
    
    if (!isAtBottom && autoScroll) {
      setAutoScroll(false);
    }
  };

  // Jump to bottom
  const jumpToBottom = () => {
    setAutoScroll(true);
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Download output as text file
  const downloadOutput = () => {
    const text = lines.map(line => `[${line.timestamp}] ${line.content}`).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${tool}_output_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Get line styling based on type
  const getLineStyle = (type: OutputLine['type']) => {
    switch (type) {
      case 'success':
        return 'text-green-400';
      case 'warning':
        return 'text-yellow-400';
      case 'error':
        return 'text-red-400';
      case 'summary':
        return 'text-cyan-300 font-semibold';
      case 'info':
      default:
        return 'text-gray-300';
    }
  };

  // Get icon for line type
  const getLineIcon = (type: OutputLine['type']) => {
    switch (type) {
      case 'success':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      case 'summary':
        return '📈';
      case 'info':
      default:
        return '';
    }
  };

  const displayLines = isExpanded ? lines : lines.slice(-50); // Show last 50 if collapsed

  return (
    <div className={`rounded-lg border border-gray-700 bg-[#0d1117] overflow-hidden shadow-lg ${isFullscreen ? 'fixed inset-4 z-50' : ''}`}>
      {/* Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-[#161b22] to-[#0d1117] border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Terminal className="h-5 w-5 text-cyan-400" />
              {isStreaming && (
                <span className="absolute -top-1 -right-1 flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                </span>
              )}
            </div>
            <div>
              <h4 className="text-sm font-semibold text-cyan-400">📊 LIVE OUTPUT</h4>
              <p className="text-xs text-gray-500">{tool.toUpperCase()} - {lines.length} lines</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Auto-scroll Toggle */}
            <button
              onClick={() => setAutoScroll(!autoScroll)}
              className={`p-1.5 rounded transition-colors ${
                autoScroll 
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' 
                  : 'hover:bg-gray-700/50 text-gray-500'
              }`}
              title={autoScroll ? 'Auto-scroll: ON' : 'Auto-scroll: OFF'}
            >
              {autoScroll ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
            </button>
            
            {/* Expand/Collapse */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 hover:bg-gray-700/50 rounded transition-colors"
              title={isExpanded ? 'Show less' : 'Show all'}
            >
              {isExpanded ? (
                <ChevronUp className="h-3.5 w-3.5 text-gray-500" />
              ) : (
                <ChevronDown className="h-3.5 w-3.5 text-gray-500" />
              )}
            </button>
            
            {/* Fullscreen Toggle */}
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1.5 hover:bg-gray-700/50 rounded transition-colors"
              title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? (
                <Minimize2 className="h-3.5 w-3.5 text-gray-500" />
              ) : (
                <Maximize2 className="h-3.5 w-3.5 text-gray-500" />
              )}
            </button>
            
            {/* Download Button */}
            <button
              onClick={downloadOutput}
              className="p-1.5 hover:bg-gray-700/50 rounded transition-colors group"
              title="Download output"
              disabled={lines.length === 0}
            >
              <Download className="h-3.5 w-3.5 text-gray-500 group-hover:text-gray-300" />
            </button>
          </div>
        </div>
      </div>

      {/* Output Content */}
      <div 
        ref={outputRef}
        onScroll={handleScroll}
        className="relative font-mono text-sm overflow-y-auto custom-scrollbar bg-black/40"
        style={{ maxHeight: isFullscreen ? 'calc(100vh - 150px)' : maxHeight }}
      >
        {lines.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-gray-600">
            <div className="text-center">
              <Terminal className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Waiting for output...</p>
            </div>
          </div>
        ) : (
          <div className="p-4 space-y-0.5">
            {displayLines.map((line, index) => (
              <div 
                key={`${line.line_number}-${index}`}
                className={`flex items-start space-x-3 py-1 hover:bg-gray-800/30 transition-colors ${getLineStyle(line.type)}`}
              >
                {/* Timestamp */}
                <span className="text-xs text-gray-600 select-none w-20 flex-shrink-0 font-mono">
                  {new Date(line.timestamp).toLocaleTimeString()}
                </span>
                
                {/* Icon */}
                {getLineIcon(line.type) && (
                  <span className="text-sm flex-shrink-0 w-5">
                    {getLineIcon(line.type)}
                  </span>
                )}
                
                {/* Content */}
                <span className="flex-1 break-all leading-relaxed">
                  {line.content}
                </span>
              </div>
            ))}
            
            {/* Auto-scroll anchor */}
            <div ref={bottomRef} />
          </div>
        )}

        {/* Terminal scanlines effect */}
        <div className="absolute inset-0 pointer-events-none opacity-5">
          <div className="h-full w-full" style={{
            backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.03) 2px, rgba(255,255,255,0.03) 4px)'
          }} />
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-[#161b22] border-t border-gray-700">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <span className={`inline-block w-2 h-2 rounded-full ${isStreaming ? 'bg-green-500 animate-pulse' : 'bg-gray-600'}`} />
              <span>{isStreaming ? 'Streaming' : 'Complete'}</span>
            </span>
            {!autoScroll && (
              <button
                onClick={jumpToBottom}
                className="text-cyan-400 hover:text-cyan-300 underline"
              >
                Jump to bottom ↓
              </button>
            )}
          </div>
          <span>
            {displayLines.length !== lines.length && `Showing last ${displayLines.length} of ${lines.length} lines`}
          </span>
        </div>
      </div>

      {/* Custom Scrollbar Styles */}
      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #0d1117;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #30363d;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #484f58;
        }
      `}</style>
    </div>
  );
};

