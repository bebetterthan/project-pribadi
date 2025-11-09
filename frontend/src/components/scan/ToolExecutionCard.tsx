/**
 * ToolExecutionCard - Visual card for tool execution
 * Shows tool metadata, parameters, and status
 */

import React from 'react';
import { Zap, CheckCircle, XCircle, Clock } from 'lucide-react';

interface ToolExecutionCardProps {
  toolName: string;
  content: string;
  metadata?: {
    function?: string;
    arguments?: Record<string, any>;
    iteration?: number;
    status?: string;
  };
}

// Tool metadata mapping
const TOOL_INFO: Record<string, { icon: string; color: string; description: string }> = {
  run_nmap: {
    icon: '🔍',
    color: 'from-amber-500/10 to-orange-500/10 border-amber-500/20',
    description: 'Network Port Scanner - Discovers open ports and services'
  },
  run_nuclei: {
    icon: '🎯',
    color: 'from-red-500/10 to-pink-500/10 border-red-500/20',
    description: 'Vulnerability Scanner - Detects CVEs and misconfigurations'
  },
  run_whatweb: {
    icon: '🌐',
    color: 'from-purple-500/10 to-indigo-500/10 border-purple-500/20',
    description: 'Technology Fingerprinting - Identifies web technologies'
  },
  run_sslscan: {
    icon: '🔒',
    color: 'from-green-500/10 to-emerald-500/10 border-green-500/20',
    description: 'SSL/TLS Analysis - Checks encryption security'
  },
  run_subfinder: {
    icon: '🔎',
    color: 'from-blue-500/10 to-cyan-500/10 border-blue-500/20',
    description: 'Subdomain Enumeration - Discovers subdomains'
  },
  run_httpx: {
    icon: '✓',
    color: 'from-green-500/10 to-teal-500/10 border-green-500/20',
    description: 'HTTP Probe - Checks host reachability'
  },
  run_ffuf: {
    icon: '📂',
    color: 'from-pink-500/10 to-rose-500/10 border-pink-500/20',
    description: 'Content Discovery - Finds hidden directories and files'
  }
};

export function ToolExecutionCard({ toolName, content, metadata }: ToolExecutionCardProps) {
  const functionName = metadata?.function || toolName;
  const toolInfo = TOOL_INFO[functionName] || {
    icon: '⚡',
    color: 'from-cyan-500/10 to-blue-500/10 border-cyan-500/20',
    description: 'Security Tool Execution'
  };

  return (
    <div className={`bg-gradient-to-r ${toolInfo.color} border rounded-lg overflow-hidden`}>
      {/* Header with Tool Info */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start space-x-3">
          <span className="text-3xl mt-0.5 animate-pulse">{toolInfo.icon}</span>
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <h4 className="text-sm font-semibold text-white">
                {functionName.replace('run_', '').toUpperCase()}
              </h4>
              {metadata?.iteration && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-gray-400">
                  Step {metadata.iteration}
                </span>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-1">
              {toolInfo.description}
            </p>
          </div>
          <div className="flex-shrink-0">
            <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="text-sm text-gray-300 font-medium mb-2">
          {content}
        </div>

        {/* Parameters */}
        {metadata?.arguments && Object.keys(metadata.arguments).length > 0 && (
          <div className="mt-3 space-y-1">
            <div className="text-xs text-gray-500 font-medium mb-1">Parameters:</div>
            <div className="bg-black/20 rounded-lg p-3 font-mono text-xs">
              {Object.entries(metadata.arguments).map(([key, value]) => (
                <div key={key} className="flex items-start space-x-2">
                  <span className="text-cyan-400 flex-shrink-0">{key}:</span>
                  <span className="text-gray-300 break-all">
                    {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

