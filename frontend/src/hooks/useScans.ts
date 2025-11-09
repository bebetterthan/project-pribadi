import apiClient from "@/lib/api";
import { Scan, ScanCreateRequest, ScanDetailsResponse } from "@/types/scan";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// ============================================================================
// Optimized React Query Hooks with Aggressive Caching
// ============================================================================

export function useScans(params?: {
  skip?: number;
  limit?: number;
  status?: string;
}) {
  const skip = params?.skip || 0;
  const limit = params?.limit || 20;

  return useQuery({
    queryKey: ["scans", skip, limit, params?.status],
    queryFn: async () => {
      const { data } = await apiClient.get(
        `/history/scans?skip=${skip}&limit=${limit}`
      );
      return data;
    },
    staleTime: 30000, // Consider data fresh for 30 seconds (increased from 10s)
    gcTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
    retry: 2,
    refetchOnWindowFocus: true, // Refresh on tab focus for latest data
    refetchOnMount: false, // Don't refetch if data is fresh
  });
}

export function useScan(scanId: string) {
  return useQuery({
    queryKey: ["scan", scanId],
    queryFn: async () => {
      const { data } = await apiClient.get<Scan>(`/scan/${scanId}`);
      return data;
    },
    refetchInterval: (query) => {
      // Smart polling - only poll if scan is running
      const data = query.state.data as Scan | undefined;
      if (data?.status === "running") {
        return 2000; // Poll every 2 seconds for running scans (faster)
      }
      return false; // Don't poll for completed scans
    },
    staleTime: (query) => {
      // Shorter stale time for running scans
      const data = query.state.data as Scan | undefined;
      return data?.status === "running" ? 1000 : 60000; // 1s for running, 1min for completed
    },
    gcTime: 10 * 60 * 1000, // Keep completed scans in cache for 10 minutes
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}

export function useScanDetails(scanId: string) {
  return useQuery({
    queryKey: ["scanDetails", scanId],
    queryFn: async () => {
      const { data } = await apiClient.get<ScanDetailsResponse>(
        `/scan/${scanId}/results`
      );
      return data;
    },
    enabled: !!scanId,
    staleTime: 60000, // Cache for 1 minute (increased from 5s)
    gcTime: 15 * 60 * 1000, // Keep in cache for 15 minutes
    retry: 3,
    // Optimistic update - use cached data while fetching
    placeholderData: (previousData) => previousData,
  });
}

export function useCreateScan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (scanData: ScanCreateRequest) => {
      const { data } = await apiClient.post<Scan>("/scan", scanData);
      return data;
    },
    onSuccess: (newScan) => {
      // Optimistic update - add new scan to cache immediately
      queryClient.setQueryData(["scan", newScan.id], newScan);

      // Invalidate list to refresh
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
  });
}

export function useDeleteScan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (scanId: string) => {
      await apiClient.delete(`/scan/${scanId}`);
    },
    onSuccess: (_, scanId) => {
      // Remove from cache immediately
      queryClient.removeQueries({ queryKey: ["scan", scanId] });
      queryClient.removeQueries({ queryKey: ["scanDetails", scanId] });

      // Invalidate list
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
  });
}
