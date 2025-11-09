/**
 * Streaming scan page - Real-time AI Agent workflow
 * Shows live thinking process like ChatGPT
 */

'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, ExternalLink, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { StreamingChat } from '@/components/scan/StreamingChat';
import { ErrorState } from '@/components/scan/ErrorState';
import { useEventStream } from '@/hooks/useEventStream';
import { useStore } from '@/store/useStore';
import toast from 'react-hot-toast';

function StreamingScanContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { geminiApiKey } = useStore();

  // Get scan parameters from URL
  const target = searchParams.get('target');
  const userPrompt = searchParams.get('prompt') || '';
  const urlApiKey = searchParams.get('apiKey');
  const tools = searchParams.get('tools')?.split(',') || ['nmap'];
  const profile = searchParams.get('profile') || 'normal';

  // Use API key from URL or store
  const effectiveApiKey = urlApiKey || geminiApiKey;

  const [scanId, setScanId] = useState<string | null>(null);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [error, setError] = useState<{ title: string; message: string; details?: string } | null>(null);
  const [progress, setProgress] = useState(0);
  const [toolsCompleted, setToolsCompleted] = useState(0);
  const [totalTools, setTotalTools] = useState(tools.length);
  const [scanCreated, setScanCreated] = useState(false); // GUARD: Prevent duplicate scan creation
  const isCreatingRef = React.useRef(false); // GUARD: Prevent concurrent requests (React Strict Mode)

  // Initialize streaming scan
  useEffect(() => {
    // GUARD 1: Prevent duplicate scan creation
    if (scanCreated) {
      console.log('⏭️ Scan already created, skipping...');
      return;
    }

    // GUARD 2: Prevent concurrent requests (React Strict Mode double-render in dev)
    if (isCreatingRef.current) {
      console.log('⏭️ Scan creation already in progress, skipping...');
      return;
    }

    // Only target is required
    if (!target) {
      console.error('❌ Missing target parameter');
      toast.error('Target is required');
      router.push('/');
      return;
    }

    console.log('🎬 Initializing streaming scan...', { target, hasPrompt: !!userPrompt, hasKey: !!effectiveApiKey });
    
    // Start the streaming scan
    startStreamingScan();
    
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, userPrompt, effectiveApiKey]); // startStreamingScan intentionally omitted to avoid re-runs

  const startStreamingScan = async () => {
    // Set guard flag
    isCreatingRef.current = true;
    
    try {
      // Use the same base URL as api.ts (already includes /api/v1)
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (effectiveApiKey) {
        headers['X-Gemini-API-Key'] = effectiveApiKey;
      }

      // Step 1: Create scan (don't add /api/v1 again, it's already in API_BASE)
      const createUrl = `${API_BASE}/scan/stream/create`;
      console.log('🚀 Creating scan...', { 
        target, 
        userPrompt: userPrompt.substring(0, 50),
        apiBase: API_BASE,
        fullUrl: createUrl,
        hasApiKey: !!effectiveApiKey,
        apiKeyLength: effectiveApiKey?.length 
      });
      
      // Create scan with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
      
      const createResponse = await fetch(createUrl, {
        method: 'POST',
        headers,
        signal: controller.signal,
        body: JSON.stringify({
          target,
          user_prompt: userPrompt,
          tools,
          profile,
          enable_ai: true,
        }),
      });
      
      clearTimeout(timeoutId);

      console.log('📥 Response received:', { 
        status: createResponse.status, 
        statusText: createResponse.statusText,
        ok: createResponse.ok 
      });

      if (!createResponse.ok) {
        const errorText = await createResponse.text();
        console.error('❌ Server error response:', errorText);
        
        let errorDetail = 'Failed to create scan';
        try {
          const errorJson = JSON.parse(errorText);
          errorDetail = errorJson.detail || errorJson.message || errorText;
        } catch {
          errorDetail = errorText || `HTTP ${createResponse.status}: ${createResponse.statusText}`;
        }
        
        setError({
          title: 'Failed to create scan',
          message: 'The backend server rejected the scan request.',
          details: errorDetail
        });
        setIsInitializing(false);
        setScanCreated(true); // GUARD: Prevent retry loop on error
        return;
      }

      const data = await createResponse.json();
      const createdScanId = data.scan_id;
      
      console.log('✅ Scan created:', { scanId: createdScanId, streamUrl: data.stream_url });

      setScanId(createdScanId);
      setScanCreated(true); // GUARD: Mark scan as created to prevent duplicates

      // Step 2: Wait a bit before connecting to SSE (give backend time to init)
      console.log('⏳ Waiting 2 seconds before SSE connection...');
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Connect to SSE stream (don't add /api/v1 again)
      const streamEndpoint = `${API_BASE}/scan/stream/${createdScanId}`;
      console.log('✅ Scan created successfully');
      console.log('🔗 Connecting to SSE:', streamEndpoint);
      
      setStreamUrl(streamEndpoint);
      setIsInitializing(false);

      toast.success('Connected to live scan!');

    } catch (error) {
      console.error('❌ Failed to start streaming scan:', error);
      
      // Log more details for debugging
      if (error instanceof Error) {
        console.error('   Error name:', error.name);
        console.error('   Error message:', error.message);
        console.error('   Error stack:', error.stack);
      }
      
      // Show user-friendly error
      let errorMessage = 'Failed to start scan';
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = '⏱️ Request timeout (60s). Backend is processing, check console logs.';
        } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
          errorMessage = 'Cannot connect to backend. Is it running on http://localhost:8000?';
        } else if (error.message.includes('API key')) {
          errorMessage = 'Invalid Gemini API key';
        } else {
          errorMessage = error.message;
        }
      }
      
      toast.error(errorMessage);
      setIsInitializing(false);
      setScanCreated(true); // GUARD: Prevent retry loop on exception
    }
  };

  const {
    messages,
    isConnected,
    error: streamError,
  } = useEventStream(streamUrl, {
    onMessage: (event) => {
      // Extract scan ID from first system message if available
      if (event.type === 'system' && event.metadata?.scan_id && !scanId) {
        setScanId(event.metadata.scan_id);
      }

      // Track progress from output events
      if (event.type === 'output' && event.metadata?.progress !== undefined) {
        setProgress(event.metadata.progress);
        if (event.metadata.completed !== undefined) {
          setToolsCompleted(event.metadata.completed);
        }
        if (event.metadata.total !== undefined) {
          setTotalTools(event.metadata.total);
        }
      }

      // Handle completion
      if (event.type === 'system' && event.metadata?.completed) {
        setProgress(100);
        toast.success('Scan completed!');
      }
    },
    onError: (err) => {
      toast.error('Stream connection failed');
      console.error(err);
    },
  });

  if (isInitializing) {
    return (
      <div className="min-h-screen bg-[#212121] flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className="text-gray-400 mb-2">Initializing AI Agent...</p>
          <p className="text-xs text-gray-600">
            Connecting to backend at {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
          </p>
          <p className="text-xs text-gray-600 mt-2">
            Check browser console (F12) for errors if stuck here
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#212121] flex items-center justify-center">
        <Card className="max-w-md p-6 text-center">
          <p className="text-red-400 mb-4">Failed to connect to streaming scan</p>
          <Button onClick={() => router.push('/')}>
            Go Home
          </Button>
        </Card>
      </div>
    );
  }

  if (streamError) {
    return (
      <div className="min-h-screen bg-[#212121] flex items-center justify-center">
        <Card className="max-w-md p-6 text-center">
          <p className="text-red-400 mb-4">Stream connection error: {streamError.message}</p>
          <Button onClick={() => window.location.reload()}>
            Retry Connection
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0a0a0a] via-[#111111] to-[#0a0a0a]">
      {/* Compact Header - ChatGPT style */}
      <div className="sticky top-0 z-50 backdrop-blur-xl bg-black/40 border-b border-white/5">
        <div className="max-w-5xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Link href="/">
                <button className="p-2 rounded-lg hover:bg-white/10 transition-colors">
                  <ArrowLeft className="w-4 h-4 text-gray-400" />
                </button>
              </Link>
              
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                  <span className="text-white text-sm font-semibold">AI</span>
                </div>
                <div>
                  <h1 className="text-sm font-medium text-white">{target}</h1>
                  <p className="text-xs text-gray-500 truncate max-w-md">{userPrompt}</p>
                </div>
              </div>
            </div>

            {scanId && (
              <Link href={`/scan/${scanId}`}>
                <button className="px-3 py-1.5 text-xs font-medium text-white bg-white/10 hover:bg-white/20 rounded-lg transition-colors flex items-center space-x-1">
                  <ExternalLink className="w-3 h-3" />
                  <span>View Full Report</span>
                </button>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Main Content - ChatGPT centered layout */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Minimalist Progress - ChatGPT style */}
        {progress > 0 && progress < 100 && (
          <div className="mb-8">
            <div className="relative">
              {/* Sleek progress bar */}
              <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
              
              {/* Mini stats */}
              <div className="flex items-center justify-between mt-3">
                <span className="text-xs text-gray-600 font-medium">
                  Analyzing • {toolsCompleted}/{totalTools} tools
                </span>
                <span className="text-xs text-gray-600 font-mono">
                  {progress}%
                </span>
              </div>
            </div>
          </div>
        )}

        <StreamingChat messages={messages} isConnected={isConnected} />
      </div>
    </div>
  );
}

// Wrap with Suspense to fix Next.js useSearchParams() requirement
export default function StreamingScanPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-600 border-t-transparent"></div>
      </div>
    }>
      <StreamingScanContent />
    </Suspense>
  );
}
