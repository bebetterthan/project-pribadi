'use client';

import Link from 'next/link';
import toast from 'react-hot-toast';
import { useScans, useDeleteScan } from '@/hooks/useScans';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { formatDate } from '@/lib/utils';
import { Trash2, Shield } from 'lucide-react';

export default function HistoryPage() {
  const { data, isLoading, error } = useScans();
  const { mutate: deleteScan } = useDeleteScan();

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this scan?')) {
      deleteScan(id, {
        onSuccess: () => {
          toast.success('Scan deleted successfully');
        },
        onError: (error: any) => {
          toast.error(`Delete failed: ${error.response?.data?.detail || error.message}`);
        },
      });
    }
  };

  // Handle different data formats
  const scans = Array.isArray(data) ? data : (data?.scans || []);
  const hasScans = scans && scans.length > 0;

  return (
    <div className="min-h-screen bg-[#0A0A0A] p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Scan History</h1>
            <p className="text-gray-400">View and manage all your penetration tests</p>
          </div>
          <Link href="/">
            <button className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl transition-all font-medium shadow-lg shadow-blue-600/30 transform hover:scale-105">
              New Scan
            </button>
          </Link>
        </div>

        <Card className="bg-[#141414] border border-gray-800 p-6">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading history...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="text-red-500 mb-2">Error loading scan history</div>
              <p className="text-gray-400 text-sm">{error?.message || 'Unknown error'}</p>
            </div>
          ) : hasScans ? (
            <div className="space-y-3">
              {scans.map((scan: any) => (
                <div
                  key={scan.id}
                  className="flex items-center justify-between p-5 bg-[#0A0A0A] border border-gray-800 rounded-xl hover:border-blue-600 hover:bg-[#1A1A1A] transition-all group"
                >
                  <Link href={`/scan/${scan.id}`} className="flex-1">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-white group-hover:text-blue-400 transition-colors text-lg">
                          {scan.target}
                        </p>
                        <p className="text-sm text-gray-400 mt-1">
                          {formatDate(scan.created_at)} • {scan.tools?.join(', ') || 'No tools'}
                        </p>
                      </div>
                      <Badge status={scan.status} />
                    </div>
                  </Link>
                  <button
                    onClick={() => handleDelete(scan.id)}
                    className="ml-4 p-2 text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
                    title="Delete scan"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <Shield className="w-16 h-16 text-gray-700 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">No scans yet</h3>
              <p className="text-gray-400 mb-6">Start your first security assessment</p>
              <Link href="/">
                <button className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl transition-all font-medium shadow-lg shadow-blue-600/30">
                  Start Your First Scan
                </button>
              </Link>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
