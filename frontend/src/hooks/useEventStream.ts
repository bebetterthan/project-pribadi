/**
 * Custom hook for Server-Sent Events (SSE) streaming
 * Used for real-time AI Agent workflow updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export interface StreamEvent {
  type: 'system' | 'thought' | 'plan' | 'tool' | 'output' | 'analysis' | 'decision' | 'function_call' | 'function_result' | 'system_info' | 'cost_report' | 'command' | 'tool_output' | 'tool_start' | 'tool_complete' | 'tool_error' | 'validation_start' | 'validation_complete' | 'escalation' | 'pro_analysis' | 'model_switch';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
  subtype?: string;  // For system_info subtypes
  // For command events
  tool?: string;
  command?: string;
  explanation?: string;
  estimated_time?: string;
  warning?: string;
  // For tool_output events
  line_number?: number;
  // For validation events
  results?: any;
  message?: string;
  total?: number;
  // For model attribution
  model?: 'flash' | 'pro';
  phase?: string;
  from?: string;
  to?: string;
  // For escalation events
  reason?: string;
  severity?: string;
  decision?: 'approved' | 'denied';
}

export interface UseStreamOptions {
  onMessage?: (event: StreamEvent) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

export function useEventStream(url: string | null, options: UseStreamOptions = {}) {
  const [messages, setMessages] = useState<StreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  
  // Use refs to stabilize callbacks and avoid re-renders
  const optionsRef = useRef(options);
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const connect = useCallback(() => {
    if (!url) return;

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    console.log('🔗 Connecting to SSE:', url);

    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('✅ SSE Connection established');
        setIsConnected(true);
        setError(null);
      };

      eventSource.onmessage = (event) => {
        try {
          const data: StreamEvent = JSON.parse(event.data);
          console.log('📨 SSE Event received:', data.type, data.content.substring(0, 50));

          setMessages((prev) => [...prev, data]);

          // Call callback if provided
          const currentOptions = optionsRef.current;
          if (currentOptions.onMessage) {
            currentOptions.onMessage(data);
          }

          // Check for completion
          if (data.type === 'system' && data.metadata?.completed) {
            console.log('✅ Scan completed, closing connection');
            if (currentOptions.onComplete) {
              currentOptions.onComplete();
            }
            // Auto-close connection on completion
            eventSource.close();
            setIsConnected(false);
          }

        } catch (err) {
          console.error('❌ Failed to parse SSE message:', err, 'Raw data:', event.data);
        }
      };

      eventSource.onerror = (err) => {
        console.error('❌ SSE Error:', err);
        console.error('   EventSource readyState:', eventSource.readyState);
        console.error('   URL:', url);
        
        // ReadyState: 0 = CONNECTING, 1 = OPEN, 2 = CLOSED
        if (eventSource.readyState === EventSource.CLOSED) {
          console.error('   Connection closed by server or network error');
        }
        
        const error = new Error('EventSource connection failed');
        setError(error);
        setIsConnected(false);
        eventSource.close();

        const currentOptions = optionsRef.current;
        if (currentOptions.onError) {
          currentOptions.onError(error);
        }
      };

    } catch (err) {
      console.error('❌ Failed to create EventSource:', err);
      const error = err instanceof Error ? err : new Error('Failed to connect');
      setError(error);
      const currentOptions = optionsRef.current;
      if (currentOptions.onError) {
        currentOptions.onError(error);
      }
    }
  }, [url]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      console.log('🔌 Closing SSE connection');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Auto-connect when URL changes
  useEffect(() => {
    if (url) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [url, connect, disconnect]); // Include all dependencies

  return {
    messages,
    isConnected,
    error,
    connect,
    disconnect,
    clearMessages,
  };
}
