/**
 * Tool Result Card Component - Display individual security tool findings
 * Fase 3: Multi-Tool Integration
 */

'use client';

import React, { useState } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Info,
  Clock,
  Terminal
} from 'lucide-react';

interface ToolResult {
  tool_name: string;
  status: 'success' | 'error' | 'warning';
  execution_time: number;
  timestamp: string;
  summary?: {
    open_ports?: number;
    vulnerabilities_found?: number;
    technologies_detected?: number;
    certificates_checked?: number;
  };
  findings?: Array<{
    severity?: 'critical' | 'high' | 'medium' | 'low' | 'info';
    title: string;
    description?: string;
  }>;
  raw_output?: string;
}

interface ToolResultCardProps {
  result: ToolResult;
}

// Tool icon helper
const getToolIcon = (toolName: string) => {
  const name = toolName.toLowerCase();
  if (name.includes('nmap')) return '🔍';
  if (name.includes('nuclei')) return '🎯';
  if (name.includes('whatweb')) return '🌐';
  if (name.includes('sslscan')) return '🔒';
  return '⚡';
};

// Severity color helper
const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'text-red-400 bg-red-500/10 border-red-500/30';
    case 'high':
      return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
    case 'medium':
      return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
    case 'low':
      return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
    case 'info':
      return 'text-gray-400 bg-gray-500/10 border-gray-500/30';
    default:
      return 'text-gray-400 bg-gray-500/10 border-gray-500/30';
  }
};

// Status icon helper
const getStatusIcon = (status: string) => {
  switch (status) {
    case 'success':
      return <CheckCircle className="w-5 h-5 text-green-400" />;
    case 'error':
      return <XCircle className="w-5 h-5 text-red-400" />;
    case 'warning':
      return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
    default:
      return <Info className="w-5 h-5 text-blue-400" />;
  }
};

export function ToolResultCard({ result }: ToolResultCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showRawOutput, setShowRawOutput] = useState(false);

  return (
    <div className="border border-gray-800 rounded-lg bg-gradient-to-br from-gray-900/50 to-gray-800/30 overflow-hidden hover:border-gray-700 transition-colors">
      {/* Card Header - Always Visible */}
      <div 
        className="p-4 cursor-pointer flex items-center justify-between"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-4">
          {/* Tool Icon */}
          <div className="text-3xl">
            {getToolIcon(result.tool_name)}
          </div>

          {/* Tool Name & Status */}
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold text-white text-lg">
                {result.tool_name}
              </h3>
              {getStatusIcon(result.status)}
            </div>
            <div className="flex items-center space-x-3 mt-1 text-xs text-gray-500">
              <span className="flex items-center">
                <Clock className="w-3 h-3 mr-1" />
                {result.execution_time.toFixed(2)}s
              </span>
              <span>
                {new Date(result.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="flex items-center space-x-4">
          {result.summary && (
            <div className="flex space-x-4 text-sm">
              {result.summary.open_ports !== undefined && (
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">{result.summary.open_ports}</div>
                  <div className="text-xs text-gray-500">Ports</div>
                </div>
              )}
              {result.summary.vulnerabilities_found !== undefined && (
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-400">{result.summary.vulnerabilities_found}</div>
                  <div className="text-xs text-gray-500">Vulns</div>
                </div>
              )}
              {result.summary.technologies_detected !== undefined && (
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-400">{result.summary.technologies_detected}</div>
                  <div className="text-xs text-gray-500">Tech</div>
                </div>
              )}
            </div>
          )}

          {/* Expand/Collapse Button */}
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          )}
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-gray-800 bg-gray-900/30">
          {/* Findings Section */}
          {result.findings && result.findings.length > 0 && (
            <div className="p-4 space-y-2">
              <h4 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wide">
                Key Findings ({result.findings.length})
              </h4>
              <div className="space-y-2">
                {result.findings.slice(0, 10).map((finding, idx) => (
                  <div 
                    key={idx}
                    className={`border rounded-md p-3 ${finding.severity ? getSeverityColor(finding.severity) : 'border-gray-700 bg-gray-800/50'}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          {finding.severity && (
                            <span className={`text-xs px-2 py-0.5 rounded uppercase font-semibold ${getSeverityColor(finding.severity)}`}>
                              {finding.severity}
                            </span>
                          )}
                          <span className="text-sm font-medium text-white">
                            {finding.title}
                          </span>
                        </div>
                        {finding.description && (
                          <p className="text-xs text-gray-400 mt-1">
                            {finding.description}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {result.findings.length > 10 && (
                  <div className="text-xs text-gray-500 text-center py-2">
                    + {result.findings.length - 10} more findings
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Raw Output Toggle */}
          {result.raw_output && (
            <div className="p-4 border-t border-gray-800">
              <button
                onClick={() => setShowRawOutput(!showRawOutput)}
                className="flex items-center space-x-2 text-sm text-gray-400 hover:text-gray-300 transition-colors"
              >
                <Terminal className="w-4 h-4" />
                <span>{showRawOutput ? 'Hide' : 'Show'} Raw Output</span>
              </button>

              {showRawOutput && (
                <pre className="mt-3 p-3 bg-black/50 border border-gray-800 rounded text-xs text-green-400 font-mono overflow-x-auto max-h-96 overflow-y-auto">
                  {result.raw_output}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

