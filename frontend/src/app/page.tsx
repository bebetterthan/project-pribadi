'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  Sparkles, 
  Zap, 
  TrendingUp, 
  RotateCcw,
  Target,
  Clock,
  CheckCircle,
  XCircle,
  Shield,
  Key,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useScans } from '@/hooks/useScans';
import { formatDistance } from 'date-fns';

export default function HomePage() {
  const router = useRouter();
  const [target, setTarget] = useState('');
  const [prompt, setPrompt] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { data, isLoading } = useScans({ limit: 3 });

  useEffect(() => {
    // Focus input on mount
    inputRef.current?.focus();
  }, []);

  const handleStartScan = () => {
    if (!target.trim()) {
      inputRef.current?.focus();
      return;
    }

    // Create scan and navigate
    const params = new URLSearchParams({
      target: target.trim(),
      ...(prompt.trim() && { prompt: prompt.trim() }),
      ...(apiKey.trim() && { apiKey: apiKey.trim() })
    });
    
    router.push(`/stream?${params.toString()}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleStartScan();
    }
  };

  const quickActions = [
    {
      icon: Zap,
      title: 'Quick Scan',
      description: 'Fast reconnaissance',
      color: '#3B82F6',
      bgColor: 'rgba(59, 130, 246, 0.1)',
      action: () => {
        setTarget('');
        setPrompt('Run a quick scan with essential tools only');
        inputRef.current?.focus();
      }
    },
    {
      icon: TrendingUp,
      title: 'Deep Scan',
      description: 'Comprehensive analysis',
      color: '#8B5CF6',
      bgColor: 'rgba(139, 92, 246, 0.1)',
      action: () => {
        setTarget('');
        setPrompt('Perform a thorough penetration test with all available tools');
        inputRef.current?.focus();
      }
    },
    {
      icon: RotateCcw,
      title: 'Rescan Last',
      description: 'Re-run previous target',
      color: '#10B981',
      bgColor: 'rgba(16, 185, 129, 0.1)',
      action: () => {
        const scans = Array.isArray(data) ? data : (data?.scans || []);
        if (scans && scans.length > 0) {
          const lastScan = scans[0];
          router.push(`/stream?target=${encodeURIComponent(lastScan.target)}`);
        }
      }
    }
  ];

  // Handle both response formats
  const scans = Array.isArray(data) ? data : (data?.scans || []);

  return (
    <div className="min-h-screen bg-[#0A0A0A]">
      {/* Main Content - Centered with generous spacing */}
      <div className="max-w-[700px] mx-auto px-6 pt-16 pb-32">
        
        {/* Hero Section - 64px spacing */}
        <div className="text-center mb-16 space-y-4">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 mb-6 shadow-lg shadow-blue-600/30">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          
          <h1 className="text-5xl font-bold text-[#F5F5F5] mb-4 tracking-tight leading-tight">
            What would you like to scan?
          </h1>
          
          <p className="text-lg text-[#A3A3A3] leading-relaxed">
            Enter a domain, IP address, or describe the security test you want to perform.
            Our AI agent will handle the rest.
          </p>
        </div>

        {/* Input Section - NO outer container, direct inputs */}
        <div className="space-y-8 mb-16">
          {/* Target Input */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-[#A3A3A3]">
              Target <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (target.trim()) handleStartScan();
                }
              }}
              placeholder="example.com or 192.168.1.1"
              className="w-full h-14 px-4 bg-[#0F0F0F] border-2 border-[#2A2A2A] rounded-xl text-[#F5F5F5] text-base placeholder-[#525252] 
                focus:outline-none focus:border-[#3B82F6] focus:ring-4 focus:ring-blue-600/10 
                transition-all duration-200 ease-out"
              autoFocus
            />
          </div>

          {/* Optional Prompt - 32px spacing from above */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-[#A3A3A3]">
              Custom Instructions <span className="text-[#737373]">(Optional)</span>
            </label>
            <textarea
              ref={inputRef}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g., Focus on web vulnerabilities, check for SQL injection..."
              rows={4}
              className="w-full px-4 py-3 bg-[#0F0F0F] border-2 border-[#2A2A2A] rounded-xl text-[#F5F5F5] placeholder-[#525252] 
                focus:outline-none focus:border-[#3B82F6] focus:ring-4 focus:ring-blue-600/10 
                transition-all duration-200 ease-out resize-none leading-relaxed"
            />
          </div>

          {/* Advanced Settings - Collapsible */}
          <div className="space-y-3">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm font-medium text-[#A3A3A3] hover:text-[#F5F5F5] transition-colors group"
            >
              {showAdvanced ? (
                <ChevronUp className="w-4 h-4 text-[#737373] group-hover:text-[#A3A3A3] transition-colors" />
              ) : (
                <ChevronDown className="w-4 h-4 text-[#737373] group-hover:text-[#A3A3A3] transition-colors" />
              )}
              <span>Advanced Settings</span>
              <span className="text-xs text-[#737373]">(API Key, Options)</span>
            </button>

            {showAdvanced && (
              <div className="space-y-4 pt-2 animate-in fade-in slide-in-from-top-2 duration-300">
                {/* API Key Input */}
                <div className="space-y-3 p-4 bg-[#0F0F0F] border border-[#2A2A2A] rounded-xl">
                  <div className="flex items-center gap-2">
                    <Key className="w-4 h-4 text-[#8B5CF6]" />
                    <label className="block text-sm font-medium text-[#A3A3A3]">
                      Gemini API Key <span className="text-[#737373]">(Optional)</span>
                    </label>
                  </div>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="AIzaSy..."
                    className="w-full h-12 px-4 bg-[#1A1A1A] border border-[#2A2A2A] rounded-lg text-[#F5F5F5] text-sm placeholder-[#525252] font-mono
                      focus:outline-none focus:border-[#8B5CF6] focus:ring-2 focus:ring-purple-600/10 
                      transition-all duration-200"
                  />
                  <p className="text-xs text-[#737373] leading-relaxed">
                    Your API key is stored locally and never sent to our servers. 
                    Get your free API key from <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300 underline">Google AI Studio</a>.
                  </p>
                </div>

                {/* Additional Options (Future) */}
                <div className="flex items-center gap-2 text-xs text-[#737373]">
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#737373]"></span>
                  <span>More options will be available here soon</span>
                </div>
              </div>
            )}
          </div>

          {/* Start Button - 32px spacing, PROMINENT */}
          <div className="space-y-3">
            <button
              onClick={handleStartScan}
              disabled={!target.trim()}
              className="w-full h-14 flex items-center justify-center gap-2 
                text-base font-semibold text-white rounded-xl
                bg-gradient-to-r from-blue-600 to-purple-600 
                hover:from-blue-700 hover:to-purple-700
                disabled:from-gray-800 disabled:to-gray-800 disabled:text-gray-500 disabled:cursor-not-allowed
                shadow-lg shadow-blue-600/30 hover:shadow-xl hover:shadow-blue-600/40
                transition-all duration-300 
                transform hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98]
                disabled:transform-none disabled:shadow-none"
            >
              <Sparkles className="w-5 h-5" />
              Start Scan
            </button>
            
            <p className="text-center text-xs text-[#737373]">
              Press <kbd className="px-2 py-1 bg-[#1A1A1A] border border-[#2A2A2A] rounded text-[#A3A3A3] font-mono">Ctrl + Enter</kbd> to start
            </p>
          </div>
        </div>

        {/* Divider - 48px spacing */}
        <div className="flex items-center gap-4 mb-12">
          <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[#2A2A2A] to-transparent" />
          <span className="text-xs text-[#737373] uppercase tracking-wider font-medium">or choose a quick action</span>
          <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[#2A2A2A] to-transparent" />
        </div>

        {/* Quick Actions - Polished cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-16">
          {quickActions.map((action, index) => {
            const Icon = action.icon;
            const isDisabled = action.title === 'Rescan Last' && (!scans || scans.length === 0);
            
            return (
              <button
                key={index}
                onClick={action.action}
                disabled={isDisabled}
                className="group p-6 bg-[#1A1A1A] border border-[#2A2A2A] rounded-2xl 
                  hover:border-[#3B82F6] hover:bg-[#222222] 
                  transition-all duration-300 text-left
                  disabled:opacity-40 disabled:cursor-not-allowed 
                  disabled:hover:border-[#2A2A2A] disabled:hover:bg-[#1A1A1A]
                  transform hover:-translate-y-1 hover:shadow-lg hover:shadow-black/20
                  disabled:transform-none"
                style={{
                  borderColor: !isDisabled ? action.color + '00' : undefined,
                }}
                onMouseEnter={(e) => {
                  if (!isDisabled) {
                    e.currentTarget.style.borderColor = action.color + '66';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#2A2A2A';
                }}
              >
                <div className="flex flex-col items-center text-center space-y-4">
                  {/* Icon with colored background */}
                  <div 
                    className="w-16 h-16 rounded-xl flex items-center justify-center 
                      group-hover:scale-110 transition-transform duration-300"
                    style={{ backgroundColor: action.bgColor }}
                  >
                    <Icon className="w-8 h-8" style={{ color: action.color }} />
                  </div>
                  
                  {/* Text */}
                  <div className="space-y-1">
                    <h3 className="font-semibold text-[#F5F5F5] group-hover:text-white transition-colors">
                      {action.title}
                    </h3>
                    <p className="text-sm text-[#A3A3A3]">
                      {action.description}
                    </p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Recent Scans - 48px spacing from above */}
        {scans && scans.length > 0 && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-[#F5F5F5]">Recent Scans</h2>
              <Link href="/history" className="text-sm text-blue-600 hover:text-blue-500 transition-colors font-medium">
                View all →
              </Link>
            </div>

            <div className="space-y-3">
              {scans.slice(0, 3).map((scan: any) => (
                <Link
                  key={scan.id}
                  href={`/scan/${scan.id}`}
                  className="block group"
                >
                  <div className="p-5 bg-[#1A1A1A] border border-[#2A2A2A] rounded-xl 
                    hover:border-[#3B82F6] hover:bg-[#222222] 
                    transition-all duration-300
                    transform hover:-translate-y-0.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        {/* Status Icon */}
                        <div className="flex-shrink-0">
                          {scan.status === 'completed' ? (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          ) : scan.status === 'failed' ? (
                            <XCircle className="w-5 h-5 text-red-500" />
                          ) : scan.status === 'running' ? (
                            <div className="w-5 h-5">
                              <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent" />
                            </div>
                          ) : (
                            <Clock className="w-5 h-5 text-gray-500" />
                          )}
                        </div>

                        {/* Scan Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Target className="w-4 h-4 text-[#737373] flex-shrink-0" />
                            <span className="font-medium text-[#F5F5F5] truncate group-hover:text-blue-400 transition-colors">
                              {scan.target}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 text-sm text-[#A3A3A3]">
                            <span>
                              {formatDistance(new Date(scan.created_at), new Date(), { addSuffix: true })}
                            </span>
                            {scan.status === 'completed' && scan.summary?.vulnerabilities && (
                              <>
                                <span className="text-[#2A2A2A]">•</span>
                                <span className="text-red-400">
                                  {scan.summary.vulnerabilities.critical || 0} critical
                                </span>
                                <span className="text-orange-400">
                                  {scan.summary.vulnerabilities.high || 0} high
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Status Badge */}
                      <Badge className={`ml-4 flex-shrink-0 ${
                        scan.status === 'completed' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                        scan.status === 'failed' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                        scan.status === 'running' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                        'bg-gray-500/10 text-gray-400 border-gray-500/20'
                      } border px-3 py-1 text-xs font-medium`}>
                        {scan.status}
                      </Badge>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Empty State for No Scans - Friendly messaging */}
        {(!scans || scans.length === 0) && !isLoading && (
          <div className="text-center py-16 px-6 bg-[#1A1A1A] border border-[#2A2A2A] rounded-2xl">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600/10 mb-6">
              <Shield className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-[#F5F5F5] mb-2">
              No scans yet
            </h3>
            <p className="text-[#A3A3A3] mb-6 max-w-sm mx-auto leading-relaxed">
              Start your first security assessment by entering a target above.
            </p>
          </div>
        )}

      </div>
    </div>
  );
}
