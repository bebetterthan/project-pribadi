'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import { useDashboard } from '@/hooks/useDashboard';
import { StatCard } from '@/components/dashboard/StatCard';
import { TrendChart } from '@/components/dashboard/TrendChart';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  Target,
  TrendingUp,
  Shield,
  AlertTriangle,
  XCircle
} from 'lucide-react';
import { formatDistance } from 'date-fns';

function DashboardContent() {
  const { overview, trends, isLoading, error } = useDashboard();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="p-8 max-w-md">
          <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-center mb-2">Failed to load dashboard</h3>
          <p className="text-gray-600 text-center">{error || 'Unknown error occurred'}</p>
        </Card>
      </div>
    );
  }

  const chartData = trends?.scans_over_time.map((scan, index) => ({
    date: new Date(scan.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    scans: scan.count,
    vulnerabilities: trends.vulnerabilities_over_time[index]?.count || 0,
  })) || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-gray-400">Welcome back! Here's your security overview.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Scans"
          value={overview.scans.total}
          subtitle={`${overview.scans.last_24h} in last 24h`}
          icon={Activity}
          color="blue"
        />
        <StatCard
          title="Open Vulnerabilities"
          value={overview.vulnerabilities.by_status.open}
          subtitle={`${overview.vulnerabilities.open_critical} critical`}
          icon={AlertTriangle}
          color="red"
        />
        <StatCard
          title="Active Assets"
          value={overview.assets.active}
          subtitle={`${overview.assets.total} total`}
          icon={Target}
          color="green"
        />
        <StatCard
          title="Success Rate"
          value={`${overview.scans.success_rate}%`}
          subtitle={`${overview.scans.completed} completed`}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* Vulnerability Breakdown */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Vulnerability Distribution</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600">{overview.vulnerabilities.by_severity.critical}</div>
            <div className="text-sm text-gray-400 mt-1">Critical</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-orange-600">{overview.vulnerabilities.by_severity.high}</div>
            <div className="text-sm text-gray-400 mt-1">High</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-600">{overview.vulnerabilities.by_severity.medium}</div>
            <div className="text-sm text-gray-400 mt-1">Medium</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{overview.vulnerabilities.by_severity.low}</div>
            <div className="text-sm text-gray-400 mt-1">Low</div>
          </div>
        </div>
      </Card>

      {/* Trends Chart */}
      {trends && chartData.length > 0 && (
        <TrendChart
          title="Activity Trends (Last 30 Days)"
          data={chartData}
          dataKeys={[
            { key: 'scans', name: 'Scans', color: '#3b82f6' },
            { key: 'vulnerabilities', name: 'Vulnerabilities', color: '#ef4444' },
          ]}
        />
      )}

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Vulnerable Assets */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Most Vulnerable Assets</h3>
          {overview.assets.top_vulnerable.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <Shield className="w-12 h-12 mx-auto mb-2 opacity-20" />
              <p className="text-sm">No vulnerable assets</p>
            </div>
          ) : (
            <div className="space-y-3">
              {overview.assets.top_vulnerable.slice(0, 5).map((asset) => (
                <div key={asset.asset_id} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-white truncate">
                      {asset.display_name || asset.target}
                    </div>
                    <div className="text-sm text-gray-400">{asset.target}</div>
                  </div>
                  <Badge className="ml-3 bg-red-100 text-red-800">
                    {asset.open_vulnerabilities} issues
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Recent Activity */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
          {overview.recent_activity.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <Clock className="w-12 h-12 mx-auto mb-2 opacity-20" />
              <p className="text-sm">No recent activity</p>
            </div>
          ) : (
            <div className="space-y-3">
              {overview.recent_activity.map((activity) => (
                <Link
                  key={activity.scan_id}
                  href={`/scan/${activity.scan_id}`}
                  className="flex items-start gap-3 p-3 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors"
                >
                  <div className="flex-shrink-0 mt-1">
                    {activity.status === 'completed' ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : activity.status === 'failed' ? (
                      <XCircle className="w-5 h-5 text-red-600" />
                    ) : (
                      <Clock className="w-5 h-5 text-yellow-600" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-white truncate">{activity.target}</div>
                    <div className="text-sm text-gray-400">
                      {formatDistance(new Date(activity.created_at), new Date(), { addSuffix: true })}
                    </div>
                  </div>
                  <Badge className={
                    activity.status === 'completed' ? 'bg-green-100 text-green-800' :
                    activity.status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }>
                    {activity.status}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="p-6 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-white mb-2">Ready to secure your infrastructure?</h3>
            <p className="text-blue-100">Start a new automated penetration test now</p>
          </div>
          <Link href="/scan">
            <Button className="bg-white text-blue-600 hover:bg-gray-100">
              Start New Scan
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-[#0f0f0f]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Suspense fallback={
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
          </div>
        }>
          <DashboardContent />
        </Suspense>
      </div>
    </div>
  );
}
