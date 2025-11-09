/**
 * Dashboard Hook - Fetch statistics and trends
 * FASE 6: Frontend UI Excellence
 */
import { useState, useEffect } from 'react';
import { API_BASE_URL } from '@/lib/constants';

export interface DashboardOverview {
  scans: {
    total: number;
    completed: number;
    running: number;
    failed: number;
    last_24h: number;
    last_7d: number;
    success_rate: number;
  };
  vulnerabilities: {
    total: number;
    by_severity: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
    by_status: {
      open: number;
      fixing: number;
      fixed: number;
    };
    open_critical: number;
  };
  assets: {
    total: number;
    active: number;
    top_vulnerable: Array<{
      asset_id: string;
      target: string;
      display_name: string | null;
      open_vulnerabilities: number;
    }>;
  };
  recent_activity: Array<{
    scan_id: string;
    target: string;
    status: string;
    created_at: string;
    completed_at: string | null;
  }>;
}

export interface TrendData {
  period_days: number;
  scans_over_time: Array<{ date: string; count: number }>;
  vulnerabilities_over_time: Array<{ date: string; count: number }>;
}

export function useDashboard() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [trends, setTrends] = useState<TrendData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        
        // Fetch overview
        const overviewRes = await fetch(`${API_BASE_URL}/dashboard/overview`);
        if (!overviewRes.ok) throw new Error('Failed to fetch overview');
        const overviewData = await overviewRes.json();
        setOverview(overviewData);

        // Fetch trends (last 30 days)
        const trendsRes = await fetch(`${API_BASE_URL}/dashboard/trends?days=30`);
        if (!trendsRes.ok) throw new Error('Failed to fetch trends');
        const trendsData = await trendsRes.json();
        setTrends(trendsData);

        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  return {
    overview,
    trends,
    isLoading,
    error,
  };
}

