'use client';

import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Globe, 
  Server, 
  Shield,
  ChevronDown,
  ChevronUp,
  ExternalLink
} from 'lucide-react';

interface ValidatedDomain {
  domain: string;
  dns_valid: boolean;
  http_accessible: boolean;
  https_accessible: boolean;
  status_code?: number;
  server?: string;
  title?: string;
  ip_address?: string;
  category: 'active' | 'partial' | 'invalid';
}

interface ValidationResults {
  total_discovered: number;
  dns_valid: number;
  dns_invalid: number;
  http_accessible: number;
  active_targets: ValidatedDomain[];
  partial_targets: ValidatedDomain[];
  invalid_targets: ValidatedDomain[];
  time_saved_percentage?: number;
}

interface EnhancedValidationDisplayProps {
  results: ValidationResults;
  toolName?: string;
}

export const EnhancedValidationDisplay: React.FC<EnhancedValidationDisplayProps> = ({
  results,
  toolName = 'SUBFINDER'
}) => {
  const [expandedSection, setExpandedSection] = useState<'active' | 'partial' | 'invalid' | null>('active');

  const toggleSection = (section: 'active' | 'partial' | 'invalid') => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 border border-gray-700 rounded-xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-indigo-900/30 to-purple-900/30 border-b border-indigo-500/20">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Shield className="h-6 w-6 text-indigo-400" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span>
            </span>
          </div>
          <div>
            <h3 className="text-lg font-bold text-indigo-200">🔍 DOMAIN VALIDATION</h3>
            <p className="text-xs text-indigo-400/70">Multi-stage filtering pipeline</p>
          </div>
        </div>
      </div>

      {/* Flow Diagram */}
      <div className="px-6 py-4 bg-black/20 border-b border-gray-700">
        <div className="flex items-center justify-between text-sm">
          <div className="text-center flex-1">
            <div className="text-2xl font-bold text-white">{results.total_discovered}</div>
            <div className="text-xs text-gray-400 mt-1">{toolName} Discovered</div>
          </div>
          
          <div className="flex items-center px-2">
            <div className="text-gray-600">→</div>
          </div>
          
          <div className="text-center flex-1">
            <div className="text-2xl font-bold text-cyan-400">{results.dns_valid}</div>
            <div className="text-xs text-gray-400 mt-1">DNS Valid</div>
          </div>
          
          <div className="flex items-center px-2">
            <div className="text-gray-600">→</div>
          </div>
          
          <div className="text-center flex-1">
            <div className="text-2xl font-bold text-green-400">{results.http_accessible}</div>
            <div className="text-xs text-gray-400 mt-1">HTTP Accessible</div>
          </div>
        </div>

        {/* Efficiency Badge */}
        {results.time_saved_percentage && results.time_saved_percentage > 0 && (
          <div className="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-green-300 text-sm">
                <CheckCircle2 className="h-4 w-4" />
                <span className="font-semibold">Smart Filtering Applied</span>
              </div>
              <div className="text-green-400 font-bold">
                ~{results.time_saved_percentage}% time saved
              </div>
            </div>
            <p className="text-xs text-green-400/70 mt-2">
              By filtering invalid targets early, we avoid wasting time scanning unreachable hosts
            </p>
          </div>
        )}
      </div>

      {/* Results Sections */}
      <div className="divide-y divide-gray-700">
        {/* Active & Accessible */}
        {results.active_targets.length > 0 && (
          <div>
            <button
              onClick={() => toggleSection('active')}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-green-500/5 transition-colors group"
            >
              <div className="flex items-center space-x-3">
                <CheckCircle2 className="h-5 w-5 text-green-400" />
                <div className="text-left">
                  <div className="font-semibold text-green-300">
                    ✅ ACTIVE & ACCESSIBLE ({results.active_targets.length})
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Fully validated targets - ready for comprehensive scanning
                  </p>
                </div>
              </div>
              {expandedSection === 'active' ? (
                <ChevronUp className="h-5 w-5 text-gray-400 group-hover:text-gray-300" />
              ) : (
                <ChevronDown className="h-5 w-5 text-gray-400 group-hover:text-gray-300" />
              )}
            </button>

            {expandedSection === 'active' && (
              <div className="px-6 pb-4 space-y-3 animate-in slide-in-from-top-2 duration-200">
                {results.active_targets.map((domain, index) => (
                  <div 
                    key={index}
                    className="bg-green-500/5 border border-green-500/20 rounded-lg p-4 hover:border-green-500/40 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <Globe className="h-4 w-4 text-green-400" />
                          <a
                            href={`https://${domain.domain}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-green-300 font-mono hover:text-green-200 flex items-center space-x-1 group"
                          >
                            <span>{domain.domain}</span>
                            <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                          </a>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="flex items-center space-x-2 text-gray-400">
                            <Server className="h-3 w-3" />
                            <span>
                              {domain.https_accessible ? 'HTTPS' : 'HTTP'} [{domain.status_code}]
                            </span>
                          </div>
                          {domain.server && (
                            <div className="text-gray-400">
                              Server: {domain.server}
                            </div>
                          )}
                          {domain.ip_address && (
                            <div className="text-gray-400">
                              IP: {domain.ip_address}
                            </div>
                          )}
                          {domain.title && (
                            <div className="text-gray-400 col-span-2">
                              Title: {domain.title}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Valid but Unresponsive */}
        {results.partial_targets.length > 0 && (
          <div>
            <button
              onClick={() => toggleSection('partial')}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-yellow-500/5 transition-colors group"
            >
              <div className="flex items-center space-x-3">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                <div className="text-left">
                  <div className="font-semibold text-yellow-300">
                    ⚠️ VALID BUT UNRESPONSIVE ({results.partial_targets.length})
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    DNS valid, HTTP timeout - will attempt port scanning only
                  </p>
                </div>
              </div>
              {expandedSection === 'partial' ? (
                <ChevronUp className="h-5 w-5 text-gray-400 group-hover:text-gray-300" />
              ) : (
                <ChevronDown className="h-5 w-5 text-gray-400 group-hover:text-gray-300" />
              )}
            </button>

            {expandedSection === 'partial' && (
              <div className="px-6 pb-4 space-y-2 animate-in slide-in-from-top-2 duration-200">
                {results.partial_targets.map((domain, index) => (
                  <div 
                    key={index}
                    className="bg-yellow-500/5 border border-yellow-500/20 rounded-lg p-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="h-3.5 w-3.5 text-yellow-400" />
                        <span className="text-yellow-300 font-mono text-sm">{domain.domain}</span>
                      </div>
                      <div className="flex items-center space-x-4 text-xs">
                        {domain.ip_address && (
                          <span className="text-gray-400">IP: {domain.ip_address}</span>
                        )}
                        <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded border border-yellow-500/30">
                          Port scan only
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Invalid */}
        {results.invalid_targets.length > 0 && (
          <div>
            <button
              onClick={() => toggleSection('invalid')}
              className="w-full px-6 py-4 flex items-center justify-between hover:bg-red-500/5 transition-colors group"
            >
              <div className="flex items-center space-x-3">
                <XCircle className="h-5 w-5 text-red-400" />
                <div className="text-left">
                  <div className="font-semibold text-red-300">
                    ❌ INVALID ({results.invalid_targets.length})
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">
                    DNS lookup failed - will be skipped entirely
                  </p>
                </div>
              </div>
              {expandedSection === 'invalid' ? (
                <ChevronUp className="h-5 w-5 text-gray-400 group-hover:text-gray-300" />
              ) : (
                <ChevronDown className="h-5 w-5 text-gray-400 group-hover:text-gray-300" />
              )}
            </button>

            {expandedSection === 'invalid' && (
              <div className="px-6 pb-4 space-y-2 animate-in slide-in-from-top-2 duration-200">
                <div className="grid grid-cols-2 gap-2">
                  {results.invalid_targets.map((domain, index) => (
                    <div 
                      key={index}
                      className="bg-red-500/5 border border-red-500/20 rounded px-3 py-2 flex items-center space-x-2"
                    >
                      <XCircle className="h-3 w-3 text-red-400 flex-shrink-0" />
                      <span className="text-red-300 font-mono text-xs truncate">{domain.domain}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer - Scan Strategy */}
      <div className="px-6 py-4 bg-gradient-to-r from-indigo-900/20 to-purple-900/20 border-t border-indigo-500/20">
        <div className="flex items-start space-x-3">
          <Shield className="h-5 w-5 text-indigo-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-indigo-200 text-sm mb-2">🎯 SCAN STRATEGY:</div>
            <div className="space-y-1.5 text-xs text-gray-300">
              <div className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span>
                <span>
                  <strong className="text-green-300">{results.active_targets.length} active targets</strong> 
                  {' '}→ Full scanning (all tools)
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-400"></span>
                <span>
                  <strong className="text-yellow-300">{results.partial_targets.length} unresponsive targets</strong>
                  {' '}→ Limited scanning (ports only)
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                <span>
                  <strong className="text-red-300">{results.invalid_targets.length} invalid targets</strong>
                  {' '}→ Skipping entirely
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

