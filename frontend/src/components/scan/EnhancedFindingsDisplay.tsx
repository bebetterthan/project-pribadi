'use client';

import React, { useState, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  AlertCircle, 
  Shield, 
  Eye, 
  Download,
  ChevronRight,
  X
} from 'lucide-react';

type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

interface Finding {
  id: string;
  title: string;
  severity: Severity;
  target: string;
  tool: string;
  description: string;
  evidence?: string;
  remediation?: string;
  cvss_score?: number;
  cve_id?: string;
}

interface EnhancedFindingsDisplayProps {
  findings: Finding[];
}

const severityConfig: Record<Severity, { color: string; bgColor: string; borderColor: string; icon: string }> = {
  critical: { 
    color: 'text-red-400', 
    bgColor: 'bg-red-500/10', 
    borderColor: 'border-red-500/30',
    icon: '🔴'
  },
  high: { 
    color: 'text-orange-400', 
    bgColor: 'bg-orange-500/10', 
    borderColor: 'border-orange-500/30',
    icon: '🟠'
  },
  medium: { 
    color: 'text-yellow-400', 
    bgColor: 'bg-yellow-500/10', 
    borderColor: 'border-yellow-500/30',
    icon: '🟡'
  },
  low: { 
    color: 'text-green-400', 
    bgColor: 'bg-green-500/10', 
    borderColor: 'border-green-500/30',
    icon: '🟢'
  },
  info: { 
    color: 'text-gray-400', 
    bgColor: 'bg-gray-500/10', 
    borderColor: 'border-gray-500/30',
    icon: '⚪'
  }
};

export const EnhancedFindingsDisplay: React.FC<EnhancedFindingsDisplayProps> = ({ findings }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSeverities, setSelectedSeverities] = useState<Severity[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);

  // Count findings by severity
  const severityCounts = useMemo(() => {
    const counts: Record<Severity, number> = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      info: 0
    };
    findings.forEach(f => counts[f.severity]++);
    return counts;
  }, [findings]);

  // Filter findings
  const filteredFindings = useMemo(() => {
    return findings.filter(finding => {
      // Search filter
      const matchesSearch = searchTerm === '' || 
        finding.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        finding.target.toLowerCase().includes(searchTerm.toLowerCase()) ||
        finding.description.toLowerCase().includes(searchTerm.toLowerCase());

      // Severity filter
      const matchesSeverity = selectedSeverities.length === 0 || 
        selectedSeverities.includes(finding.severity);

      return matchesSearch && matchesSeverity;
    });
  }, [findings, searchTerm, selectedSeverities]);

  // Toggle severity filter
  const toggleSeverity = (severity: Severity) => {
    setSelectedSeverities(prev =>
      prev.includes(severity)
        ? prev.filter(s => s !== severity)
        : [...prev, severity]
    );
  };

  // Export findings
  const exportFindings = () => {
    const data = filteredFindings.map(f => ({
      severity: f.severity.toUpperCase(),
      title: f.title,
      target: f.target,
      tool: f.tool,
      description: f.description,
      cvss: f.cvss_score,
      cve: f.cve_id
    }));
    
    const json = JSON.stringify(data, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `findings_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 border border-gray-700 rounded-xl overflow-hidden shadow-xl">
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-red-900/30 to-orange-900/30 border-b border-red-500/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="h-6 w-6 text-red-400" />
              <div>
                <h3 className="text-lg font-bold text-white">🔍 FINDINGS</h3>
                <p className="text-xs text-gray-400">{filteredFindings.length} of {findings.length} findings</p>
              </div>
            </div>
            
            <button
              onClick={exportFindings}
              className="flex items-center space-x-2 px-3 py-1.5 bg-gray-700/50 hover:bg-gray-700 rounded border border-gray-600 transition-colors text-sm text-gray-300"
            >
              <Download className="h-4 w-4" />
              <span>Export JSON</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="px-6 py-4 bg-black/20 border-b border-gray-700 space-y-3">
          {/* Severity Filter */}
          <div className="flex flex-wrap gap-2">
            {(Object.keys(severityConfig) as Severity[]).map(severity => {
              const config = severityConfig[severity];
              const count = severityCounts[severity];
              const isSelected = selectedSeverities.includes(severity);
              
              return (
                <button
                  key={severity}
                  onClick={() => toggleSeverity(severity)}
                  className={`px-3 py-1.5 rounded-lg border transition-all text-sm font-medium ${
                    isSelected
                      ? `${config.bgColor} ${config.color} ${config.borderColor}`
                      : 'bg-gray-800/50 text-gray-500 border-gray-700 hover:border-gray-600'
                  }`}
                  disabled={count === 0}
                >
                  <span className="mr-1">{config.icon}</span>
                  <span className="capitalize">{severity}</span>
                  <span className="ml-1.5 opacity-70">({count})</span>
                </button>
              );
            })}
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search findings..."
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors"
            />
          </div>
        </div>

        {/* Findings List */}
        <div className="divide-y divide-gray-700 max-h-[600px] overflow-y-auto custom-scrollbar">
          {filteredFindings.length === 0 ? (
            <div className="px-6 py-12 text-center text-gray-500">
              <Shield className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No findings match your filters</p>
            </div>
          ) : (
            filteredFindings.map((finding) => {
              const config = severityConfig[finding.severity];
              
              return (
                <div
                  key={finding.id}
                  onClick={() => setSelectedFinding(finding)}
                  className="px-6 py-4 hover:bg-white/5 cursor-pointer transition-colors group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="text-xl">{config.icon}</span>
                        <div className="flex-1">
                          <h4 className="font-semibold text-white group-hover:text-cyan-300 transition-colors">
                            {finding.title}
                          </h4>
                          <div className="flex items-center space-x-3 mt-1 text-xs text-gray-400">
                            <span>Target: {finding.target}</span>
                            <span>•</span>
                            <span>Tool: {finding.tool}</span>
                            {finding.cvss_score && (
                              <>
                                <span>•</span>
                                <span>CVSS: {finding.cvss_score}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      <p className="text-sm text-gray-300 line-clamp-2 pl-8">
                        {finding.description}
                      </p>
                    </div>
                    
                    <div className="ml-4 flex items-center space-x-2">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${config.bgColor} ${config.color} ${config.borderColor} border capitalize`}>
                        {finding.severity}
                      </span>
                      <ChevronRight className="h-5 w-5 text-gray-600 group-hover:text-gray-400 transition-colors" />
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Finding Detail Modal */}
      {selectedFinding && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl">
            {/* Modal Header */}
            <div className={`px-6 py-4 border-b ${severityConfig[selectedFinding.severity].borderColor} ${severityConfig[selectedFinding.severity].bgColor}`}>
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <span className="text-2xl">{severityConfig[selectedFinding.severity].icon}</span>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-white mb-2">{selectedFinding.title}</h3>
                    <div className="flex flex-wrap gap-2 text-sm">
                      <span className={`px-3 py-1 rounded-full ${severityConfig[selectedFinding.severity].bgColor} ${severityConfig[selectedFinding.severity].color} border ${severityConfig[selectedFinding.severity].borderColor} font-semibold capitalize`}>
                        {selectedFinding.severity} Severity
                      </span>
                      {selectedFinding.cvss_score && (
                        <span className="px-3 py-1 rounded-full bg-gray-800 text-gray-300 border border-gray-700">
                          CVSS {selectedFinding.cvss_score}
                        </span>
                      )}
                      {selectedFinding.cve_id && (
                        <span className="px-3 py-1 rounded-full bg-gray-800 text-gray-300 border border-gray-700">
                          {selectedFinding.cve_id}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedFinding(null)}
                  className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <X className="h-5 w-5 text-gray-400" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)] custom-scrollbar space-y-6">
              {/* Overview */}
              <div>
                <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">Overview</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Target:</span>
                    <span className="ml-2 text-white font-mono">{selectedFinding.target}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Detected by:</span>
                    <span className="ml-2 text-white">{selectedFinding.tool}</span>
                  </div>
                </div>
              </div>

              {/* Description */}
              <div>
                <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">Description</h4>
                <p className="text-gray-300 leading-relaxed">{selectedFinding.description}</p>
              </div>

              {/* Evidence */}
              {selectedFinding.evidence && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">Evidence</h4>
                  <div className="bg-black/40 border border-gray-700 rounded-lg p-4">
                    <pre className="text-sm text-gray-300 font-mono overflow-x-auto">
                      {selectedFinding.evidence}
                    </pre>
                  </div>
                </div>
              )}

              {/* Remediation */}
              {selectedFinding.remediation && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">Remediation</h4>
                  <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                    <p className="text-green-300 leading-relaxed">{selectedFinding.remediation}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 bg-gray-800/50 border-t border-gray-700 flex justify-end space-x-2">
              <button
                onClick={() => setSelectedFinding(null)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Scrollbar styles */}
      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #1a1a1a;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #3a3a3a;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #4a4a4a;
        }
      `}</style>
    </>
  );
};

