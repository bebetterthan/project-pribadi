/**
 * Vulnerabilities Table Component - Display security findings in sortable table
 * Fase 3: Multi-Tool Integration
 */

'use client';

import React, { useState, useMemo } from 'react';
import { 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp,
  Filter,
  Search,
  ExternalLink
} from 'lucide-react';

interface Vulnerability {
  id: string;
  tool_source: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description?: string;
  cve?: string;
  cvss_score?: number;
  affected_endpoint?: string;
  remediation?: string;
  reference_url?: string;
}

interface VulnerabilitiesTableProps {
  vulnerabilities: Vulnerability[];
}

// Severity colors
const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'text-red-400 bg-red-500/10';
    case 'high':
      return 'text-orange-400 bg-orange-500/10';
    case 'medium':
      return 'text-yellow-400 bg-yellow-500/10';
    case 'low':
      return 'text-blue-400 bg-blue-500/10';
    case 'info':
      return 'text-gray-400 bg-gray-500/10';
    default:
      return 'text-gray-400 bg-gray-500/10';
  }
};

// Severity priority for sorting
const getSeverityPriority = (severity: string) => {
  switch (severity) {
    case 'critical': return 5;
    case 'high': return 4;
    case 'medium': return 3;
    case 'low': return 2;
    case 'info': return 1;
    default: return 0;
  }
};

export function VulnerabilitiesTable({ vulnerabilities }: VulnerabilitiesTableProps) {
  const [sortBy, setSortBy] = useState<'severity' | 'tool' | 'title'>('severity');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterSeverity, setFilterSeverity] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // Toggle sort
  const handleSort = (column: 'severity' | 'tool' | 'title') => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  // Toggle severity filter
  const toggleSeverityFilter = (severity: string) => {
    setFilterSeverity(prev => 
      prev.includes(severity) 
        ? prev.filter(s => s !== severity)
        : [...prev, severity]
    );
  };

  // Toggle row expansion
  const toggleRowExpansion = (id: string) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  // Filtered and sorted vulnerabilities
  const displayedVulnerabilities = useMemo(() => {
    let filtered = vulnerabilities;

    // Apply severity filter
    if (filterSeverity.length > 0) {
      filtered = filtered.filter(v => filterSeverity.includes(v.severity));
    }

    // Apply search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(v => 
        v.title.toLowerCase().includes(query) ||
        v.description?.toLowerCase().includes(query) ||
        v.cve?.toLowerCase().includes(query)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      
      if (sortBy === 'severity') {
        comparison = getSeverityPriority(b.severity) - getSeverityPriority(a.severity);
      } else if (sortBy === 'tool') {
        comparison = a.tool_source.localeCompare(b.tool_source);
      } else if (sortBy === 'title') {
        comparison = a.title.localeCompare(b.title);
      }

      return sortOrder === 'asc' ? -comparison : comparison;
    });

    return filtered;
  }, [vulnerabilities, sortBy, sortOrder, filterSeverity, searchQuery]);

  // Severity count
  const severityCounts = useMemo(() => {
    return vulnerabilities.reduce((acc, v) => {
      acc[v.severity] = (acc[v.severity] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [vulnerabilities]);

  return (
    <div className="space-y-4">
      {/* Header with stats */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Security Findings</h2>
          <p className="text-sm text-gray-500 mt-1">
            {displayedVulnerabilities.length} of {vulnerabilities.length} vulnerabilities
          </p>
        </div>
        
        {/* Severity badges */}
        <div className="flex items-center space-x-2">
          {['critical', 'high', 'medium', 'low', 'info'].map(severity => {
            const count = severityCounts[severity] || 0;
            if (count === 0) return null;
            
            return (
              <button
                key={severity}
                onClick={() => toggleSeverityFilter(severity)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase transition-all ${
                  getSeverityColor(severity)
                } ${
                  filterSeverity.includes(severity)
                    ? 'ring-2 ring-white/20 scale-105'
                    : 'opacity-60 hover:opacity-100'
                }`}
              >
                {severity} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
        <input
          type="text"
          placeholder="Search vulnerabilities (title, description, CVE)..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-3 bg-gray-900/50 border border-gray-800 rounded-lg text-gray-300 placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all"
        />
      </div>

      {/* Table */}
      {displayedVulnerabilities.length === 0 ? (
        <div className="text-center py-12 bg-gray-900/30 border border-gray-800 rounded-lg">
          <AlertTriangle className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500">No vulnerabilities found matching your criteria</p>
        </div>
      ) : (
        <div className="border border-gray-800 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-900/50 border-b border-gray-800">
              <tr>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('severity')}
                    className="flex items-center space-x-1 text-xs font-semibold text-gray-400 uppercase tracking-wide hover:text-gray-300 transition-colors"
                  >
                    <span>Severity</span>
                    {sortBy === 'severity' && (
                      sortOrder === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                </th>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('title')}
                    className="flex items-center space-x-1 text-xs font-semibold text-gray-400 uppercase tracking-wide hover:text-gray-300 transition-colors"
                  >
                    <span>Finding</span>
                    {sortBy === 'title' && (
                      sortOrder === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                </th>
                <th className="px-4 py-3 text-left">
                  <button
                    onClick={() => handleSort('tool')}
                    className="flex items-center space-x-1 text-xs font-semibold text-gray-400 uppercase tracking-wide hover:text-gray-300 transition-colors"
                  >
                    <span>Tool</span>
                    {sortBy === 'tool' && (
                      sortOrder === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">
                  CVSS
                </th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {displayedVulnerabilities.map((vuln) => {
                const isExpanded = expandedRows.has(vuln.id);
                
                return (
                  <React.Fragment key={vuln.id}>
                    <tr className="hover:bg-gray-900/30 transition-colors">
                      <td className="px-4 py-3">
                        <span className={`inline-block px-2.5 py-1 rounded text-xs font-semibold uppercase ${getSeverityColor(vuln.severity)}`}>
                          {vuln.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-300 font-medium">
                          {vuln.title}
                        </div>
                        {vuln.cve && (
                          <div className="text-xs text-gray-500 mt-0.5 font-mono">
                            {vuln.cve}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs text-gray-500 font-mono">
                          {vuln.tool_source}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {vuln.cvss_score && (
                          <span className="text-sm text-gray-400 font-mono">
                            {vuln.cvss_score.toFixed(1)}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => toggleRowExpansion(vuln.id)}
                          className="text-gray-500 hover:text-gray-300 transition-colors"
                        >
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5" />
                          ) : (
                            <ChevronDown className="w-5 h-5" />
                          )}
                        </button>
                      </td>
                    </tr>
                    
                    {/* Expanded row details */}
                    {isExpanded && (
                      <tr className="bg-gray-900/50">
                        <td colSpan={5} className="px-4 py-4">
                          <div className="space-y-3 max-w-4xl">
                            {vuln.description && (
                              <div>
                                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">
                                  Description
                                </h4>
                                <p className="text-sm text-gray-300 leading-relaxed">
                                  {vuln.description}
                                </p>
                              </div>
                            )}
                            
                            {vuln.affected_endpoint && (
                              <div>
                                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">
                                  Affected Endpoint
                                </h4>
                                <code className="text-sm text-blue-400 font-mono bg-blue-500/10 px-2 py-1 rounded">
                                  {vuln.affected_endpoint}
                                </code>
                              </div>
                            )}
                            
                            {vuln.remediation && (
                              <div>
                                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">
                                  Remediation
                                </h4>
                                <p className="text-sm text-gray-300 leading-relaxed">
                                  {vuln.remediation}
                                </p>
                              </div>
                            )}
                            
                            {vuln.reference_url && (
                              <div>
                                <a
                                  href={vuln.reference_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center space-x-1 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                                >
                                  <span>Learn More</span>
                                  <ExternalLink className="w-4 h-4" />
                                </a>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

