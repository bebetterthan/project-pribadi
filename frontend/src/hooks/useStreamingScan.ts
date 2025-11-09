/**
 * Hook for creating streaming scans with SSE
 */

import { useMutation } from '@tanstack/react-query';
import { ScanCreateRequest } from '@/types/scan';
import { useStore } from '@/store/useStore';

export function useCreateStreamingScan() {
  const { geminiApiKey } = useStore();

  return useMutation({
    mutationFn: async (data: ScanCreateRequest): Promise<{ scanId: string; streamUrl: string }> => {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      // Create the scan via streaming endpoint
      // This will return immediately with scan ID, and we'll connect to SSE separately

      // For now, we'll use a different approach:
      // We'll just return the stream URL, and let the component handle connection

      // Generate scan ID (will be created by backend when SSE connects)
      const streamUrl = `${API_BASE}/api/v1/scan/stream`;

      // We need to make a POST request to create the scan first
      // But for streaming, we'll do it via SSE connection directly

      return {
        scanId: 'pending', // Will be updated when SSE connects
        streamUrl: buildStreamUrl(streamUrl, data, geminiApiKey),
      };
    },
  });
}

function buildStreamUrl(baseUrl: string, data: ScanCreateRequest, apiKey: string | null): string {
  // For SSE, we can't send POST body, so we need to pass data as query params
  // But that's not ideal... Let's use a different approach

  // Better: Make a regular POST to create the scan, then return streaming endpoint
  return baseUrl;
}

/**
 * Alternative: Create scan first, then get stream URL
 */
export async function createStreamingScan(
  data: ScanCreateRequest,
  geminiApiKey: string | null
): Promise<string> {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (geminiApiKey) {
    headers['X-Gemini-API-Key'] = geminiApiKey;
  }

  const response = await fetch(`${API_BASE}/api/v1/scan/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create scan' }));
    throw new Error(error.detail || 'Failed to create streaming scan');
  }

  // This endpoint returns SSE stream, but we need the scan ID first
  // Let's modify the backend to return scan ID in first event

  // For now, return the response as-is (it's an EventSource-compatible endpoint)
  return response.url;
}
