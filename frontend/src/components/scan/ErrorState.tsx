import React from 'react';
import Link from 'next/link';
import { AlertCircle, RefreshCw, Home, Settings } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface ErrorStateProps {
  title: string;
  message: string;
  details?: string;
  onRetry?: () => void;
  showHome?: boolean;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title,
  message,
  details,
  onRetry,
  showHome = true,
}) => {
  return (
    <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center p-6">
      <Card className="max-w-lg w-full p-8 bg-[#1A1A1A] border border-red-900/20">
        <div className="text-center space-y-6">
          {/* Icon */}
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-600/10">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>

          {/* Title */}
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">{title}</h2>
            <p className="text-[#A3A3A3] leading-relaxed">{message}</p>
          </div>

          {/* Details (if any) */}
          {details && (
            <div className="p-4 bg-[#0F0F0F] border border-red-900/30 rounded-xl">
              <p className="text-sm text-red-400 font-mono text-left break-all">
                {details}
              </p>
            </div>
          )}

          {/* Troubleshooting Tips */}
          <div className="text-left space-y-2 p-4 bg-[#0F0F0F] border border-[#2A2A2A] rounded-xl">
            <div className="flex items-start gap-2 text-sm text-[#A3A3A3]">
              <Settings className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
              <span>Make sure the backend server is running on port 8000</span>
            </div>
            <div className="flex items-start gap-2 text-sm text-[#A3A3A3]">
              <Settings className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
              <span>Check if Gemini API key is configured (optional)</span>
            </div>
            <div className="flex items-start gap-2 text-sm text-[#A3A3A3]">
              <Settings className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
              <span>Verify target is reachable and valid</span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 justify-center">
            {onRetry && (
              <Button
                onClick={onRetry}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry
              </Button>
            )}
            {showHome && (
              <Link href="/">
                <Button className="bg-[#2A2A2A] hover:bg-[#3A3A3A] text-white">
                  <Home className="w-4 h-4 mr-2" />
                  Go Home
                </Button>
              </Link>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};

