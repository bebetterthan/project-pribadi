'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useScan, useScanDetails } from '@/hooks/useScans';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { AnalysisDisplay } from '@/components/analysis/AnalysisDisplay';
import { ScanProgress } from '@/components/scan/ScanProgress';
import AgentThoughts from '@/components/scan/AgentThoughts';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { formatDate, formatDuration } from '@/lib/utils';
import { ArrowLeft, Loader2 } from 'lucide-react';

export default function ScanDetailClient({ scanId }: { scanId: string }) {
  const { data: scan, isLoading: scanLoading } = useScan(scanId);
  const { data: details, isLoading: detailsLoading } = useScanDetails(scanId);
  const [prevStatus, setPrevStatus] = useState<string | null>(null);
  const [showSuccessToast, setShowSuccessToast] = useState(false);

  const scanData = scan as any;

  // Auto-show success message when scan completes
  useEffect(() => {
    if (scanData && prevStatus === 'running' && scanData.status === 'completed') {
      setShowSuccessToast(true);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    if (scanData) {
      setPrevStatus(scanData.status);
    }
  }, [scanData?.status, prevStatus, scanData]);

  if (scanLoading || detailsLoading) {
    return (
      <div className="min-h-screen bg-[#212121] flex justify-center items-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-green-500 mx-auto mb-4" />
          <p className="text-gray-400">Loading scan details...</p>
        </div>
      </div>
    );
  }

  if (!scanData) {
    return (
      <div className="min-h-screen bg-[#212121] flex justify-center items-center">
        <div className="text-center">
          <p className="text-xl text-white mb-2">Scan not found</p>
          <Link href="/">
            <Button variant="primary">Go Home</Button>
          </Link>
        </div>
      </div>
    );
  }

  const isRunning = scanData.status === 'running';
  const isPending = scanData.status === 'pending';
  const isCompleted = scanData.status === 'completed';
  const isFailed = scanData.status === 'failed';

  return (
    <ErrorBoundary>
    <div className="min-h-screen bg-[#212121]">
      {/* Fixed Header */}
      <div className="sticky top-0 z-10 bg-[#171717] border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/">
              <button className="p-2 bg-[#2f2f2f] hover:bg-[#3a3a3a] border border-[#565656] rounded-lg transition-colors">
                <ArrowLeft className="h-4 w-4 text-gray-400" />
              </button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-white">{scanData.target}</h1>
              <div className="flex items-center space-x-4 mt-1">
                <p className="text-gray-400 text-xs">
                  Created: {formatDate(scanData.created_at)}
                </p>
                {scanData.started_at && (
                  <p className="text-gray-400 text-xs">
                    Started: {formatDate(scanData.started_at)}
                  </p>
                )}
                {scanData.completed_at && (
                  <p className="text-gray-400 text-xs">
                    Completed: {formatDate(scanData.completed_at)}
                  </p>
                )}
              </div>
            </div>
          </div>
          <Badge status={scanData.status} />
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Success Banner */}
        {showSuccessToast && isCompleted && (
          <div className="bg-green-900/20 border border-green-600/30 rounded-xl p-6 animate-pulse">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-3xl">✅</span>
                <div>
                  <h3 className="text-lg font-semibold text-green-400">Scan Completed Successfully!</h3>
                  <p className="text-green-300 text-sm mt-1">All tools have finished execution. Results are ready below.</p>
                </div>
              </div>
              <button
                onClick={() => setShowSuccessToast(false)}
                className="text-green-400 hover:text-green-300 text-2xl"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Pending State */}
        {isPending && (
          <div className="bg-yellow-900/20 border border-yellow-600/30 rounded-xl p-6">
            <div className="flex items-center space-x-3">
              <Loader2 className="h-5 w-5 text-yellow-400 animate-spin" />
              <div>
                <h3 className="text-lg font-semibold text-yellow-400">Scan Queued</h3>
                <p className="text-yellow-300 text-sm mt-1">Waiting to start...</p>
              </div>
            </div>
          </div>
        )}

        {/* AI Agent Thought Process - NEW: ReAct Pattern */}
        {scanData.agent_thoughts && scanData.agent_thoughts.length > 0 && (
          <>
            <AgentThoughts thoughts={scanData.agent_thoughts} />
          </>
        )}

        {/* AI Strategy Display - Fallback for non-agent mode */}
        {scanData.ai_strategy && !scanData.agent_thoughts && (
          <div className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-blue-600/30 rounded-xl p-6">
            <div className="flex items-center space-x-2 mb-4">
              <span className="text-2xl">🤖</span>
              <h3 className="text-lg font-semibold text-blue-300">AI Strategic Planning</h3>
            </div>

            <div className="space-y-4">
              {/* Reasoning */}
              <div>
                <h4 className="text-sm font-semibold text-blue-400 mb-2">🧠 Reasoning:</h4>
                <p className="text-sm text-gray-300 bg-[#1a1a1a] p-3 rounded-lg">
                  {scanData.ai_strategy.reasoning}
                </p>
              </div>

              {/* Attack Plan */}
              <div>
                <h4 className="text-sm font-semibold text-purple-400 mb-2">⚔️ Attack Plan:</h4>
                <p className="text-sm text-gray-300 bg-[#1a1a1a] p-3 rounded-lg whitespace-pre-wrap">
                  {scanData.ai_strategy.attack_plan}
                </p>
              </div>

              {/* Expected Findings */}
              {scanData.ai_strategy.expected_findings && scanData.ai_strategy.expected_findings.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-green-400 mb-2">🎯 Expected Findings:</h4>
                  <ul className="space-y-1 bg-[#1a1a1a] p-3 rounded-lg">
                    {scanData.ai_strategy.expected_findings.map((finding: string, i: number) => (
                      <li key={i} className="text-sm text-gray-300 flex items-start space-x-2">
                        <span className="text-green-400">•</span>
                        <span>{finding}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Running State with Progress */}
        {isRunning && (
          <div className="bg-[#2f2f2f] border border-[#565656] rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
              <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />
              <span>Scan in Progress</span>
            </h3>
            <ScanProgress
              currentTool={scanData.current_tool || undefined}
              completedTools={details?.results.map((r: any) => r.tool_name) || []}
              allTools={scanData.tools}
            />
          </div>
        )}

        {/* Failed State */}
        {isFailed && (
          <div className="bg-red-900/20 border border-red-600/30 rounded-xl p-6">
            <div className="flex items-center space-x-3">
              <span className="text-3xl">❌</span>
              <div>
                <h3 className="text-lg font-semibold text-red-400">Scan Failed</h3>
                <p className="text-red-300 text-sm mt-1">{scanData.error_message || 'An error occurred during scanning'}</p>
              </div>
            </div>
          </div>
        )}

        {/* Summary Statistics */}
        {(isCompleted || isRunning) && details && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm">Tools Executed</p>
                    <p className="text-3xl font-bold text-white mt-1">{details.results.length}</p>
                  </div>
                  <span className="text-4xl">🔧</span>
                </div>
              </div>
            </Card>

            <Card>
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm">Total Findings</p>
                    <p className="text-3xl font-bold text-white mt-1">
                      {details.results.reduce((acc: number, r: any) => {
                        if (r.tool_name === 'nuclei' && r.parsed_output?.findings) {
                          return acc + r.parsed_output.findings.length;
                        }
                        if (r.tool_name === 'nmap' && r.parsed_output?.open_ports) {
                          return acc + r.parsed_output.open_ports.length;
                        }
                        return acc;
                      }, 0)}
                    </p>
                  </div>
                  <span className="text-4xl">🎯</span>
                </div>
              </div>
            </Card>

            <Card>
              <div className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-400 text-sm">Duration</p>
                    <p className="text-3xl font-bold text-white mt-1">
                      {scanData.started_at && scanData.completed_at
                        ? formatDuration(scanData.started_at, scanData.completed_at)
                        : scanData.started_at
                        ? formatDuration(scanData.started_at, new Date().toISOString())
                        : 'N/A'}
                    </p>
                  </div>
                  <span className="text-4xl">⏱️</span>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Tool Results */}
        {details && details.results && details.results.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
              <span>🔍</span>
              <span>Scan Results</span>
            </h2>

            {details.results.map((result: any) => (
              <Card key={result.id}>
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="bg-blue-600/20 border border-blue-600/50 rounded-lg p-2">
                        <span className="text-lg">🔧</span>
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">{result.tool_name.toUpperCase()}</h3>
                        <p className="text-xs text-gray-400">
                          Exit Code: {result.exit_code} • Duration: {result.execution_time.toFixed(2)}s
                        </p>
                      </div>
                    </div>
                  </div>

                  {result.parsed_output ? (
                    <div className="bg-[#1a1a1a] rounded-lg p-4 border border-[#565656]">
                      <pre className="text-gray-300 text-xs font-mono overflow-x-auto whitespace-pre-wrap">
                        {JSON.stringify(result.parsed_output, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <div className="bg-[#1a1a1a] rounded-lg p-4 border border-[#565656]">
                      <p className="text-gray-400 text-sm">No parsed output available</p>
                    </div>
                  )}

                  {result.error_message && (
                    <div className="mt-4 bg-red-900/20 border border-red-600/30 rounded-lg p-4">
                      <p className="text-red-400 text-sm">{result.error_message}</p>
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* AI Analysis */}
        {details && details.analysis && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center space-x-2">
              <span>🤖</span>
              <span>AI Analysis</span>
            </h2>
            <AnalysisDisplay analysis={details.analysis} />
          </div>
        )}
      </div>
    </div>
    </ErrorBoundary>
  );
}
