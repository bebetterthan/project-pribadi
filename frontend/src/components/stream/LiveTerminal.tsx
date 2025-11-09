/**
 * Live Terminal View - Real-time tool output display
 * Like watching a terminal in real-time
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import { Copy, Download, Maximize2, Minimize2 } from 'lucide-react';

interface TerminalLine {
  content: string;
  type: 'command' | 'output' | 'error' | 'success' | 'warning' | 'info';
  timestamp: string;
}

interface LiveTerminalProps {
  lines: TerminalLine[];
  title?: string;
  autoScroll?: boolean;
  maxLines?: number;
}

export function LiveTerminal({ 
  lines, 
  title = 'Terminal Output',
  autoScroll = true,
  maxLines = 1000 
}: LiveTerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(autoScroll);

  // Auto-scroll to bottom when new lines arrive
  useEffect(() => {
    if (autoScrollEnabled && terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [lines, autoScrollEnabled]);

  // Limit lines to prevent memory issues
  const displayLines = lines.slice(-maxLines);

  const copyToClipboard = () => {
    const text = displayLines.map(line => line.content).join('\n');
    navigator.clipboard.writeText(text);
  };

  const downloadLog = () => {
    const text = displayLines.map(line => 
      `[${new Date(line.timestamp).toLocaleTimeString()}] ${line.content}`
    ).join('\n');
    
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scan-log-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getLineColor = (type: TerminalLine['type']) => {
    switch (type) {
      case 'command':
        return 'text-yellow-400 font-semibold';
      case 'error':
        return 'text-red-400';
      case 'success':
        return 'text-green-400';
      case 'warning':
        return 'text-orange-400';
      case 'info':
        return 'text-blue-400';
      default:
        return 'text-gray-300';
    }
  };

  return (
    <div className={`
      bg-[#0d1117] border border-gray-700 rounded-lg overflow-hidden
      ${isFullscreen ? 'fixed inset-4 z-50' : 'relative'}
    `}>
      {/* Terminal Header */}
      <div className="bg-[#161b22] border-b border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          <span className="text-sm font-medium text-gray-300 ml-3">{title}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAutoScrollEnabled(!autoScrollEnabled)}
            className={`p-1.5 rounded hover:bg-gray-700 transition-colors ${
              autoScrollEnabled ? 'text-green-400' : 'text-gray-500'
            }`}
            title={autoScrollEnabled ? 'Auto-scroll enabled' : 'Auto-scroll disabled'}
          >
            <span className="text-xs">↓</span>
          </button>
          
          <button
            onClick={copyToClipboard}
            className="p-1.5 text-gray-400 hover:text-white rounded hover:bg-gray-700 transition-colors"
            title="Copy all"
          >
            <Copy className="w-4 h-4" />
          </button>
          
          <button
            onClick={downloadLog}
            className="p-1.5 text-gray-400 hover:text-white rounded hover:bg-gray-700 transition-colors"
            title="Download log"
          >
            <Download className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-1.5 text-gray-400 hover:text-white rounded hover:bg-gray-700 transition-colors"
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Terminal Content */}
      <div 
        ref={terminalRef}
        className={`
          font-mono text-sm overflow-y-auto p-4 space-y-0.5
          ${isFullscreen ? 'h-[calc(100vh-8rem)]' : 'h-96'}
        `}
        style={{
          scrollbarWidth: 'thin',
          scrollbarColor: '#374151 #1f2937'
        }}
      >
        {displayLines.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            Waiting for output...
          </div>
        ) : (
          displayLines.map((line, index) => (
            <div
              key={index}
              className={`
                ${getLineColor(line.type)}
                hover:bg-gray-800/30 px-2 -mx-2 rounded
                transition-colors
                animate-in fade-in slide-in-from-left-2
                duration-150
              `}
            >
              {line.type === 'command' && (
                <span className="text-green-500 mr-2">$</span>
              )}
              {line.content}
            </div>
          ))
        )}
        
        {/* Streaming indicator */}
        {lines.length > 0 && autoScrollEnabled && (
          <div className="flex items-center space-x-2 text-green-400 text-xs mt-2">
            <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
            <span>Live streaming...</span>
          </div>
        )}
      </div>

      {/* Terminal Footer */}
      <div className="bg-[#161b22] border-t border-gray-700 px-4 py-1.5 flex items-center justify-between text-xs text-gray-500">
        <span>{displayLines.length} lines</span>
        <span>
          {lines.length > maxLines && `(showing last ${maxLines})`}
        </span>
      </div>
    </div>
  );
}

