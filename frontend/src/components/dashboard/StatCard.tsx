import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Card } from '@/components/ui/Card';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color: 'blue' | 'red' | 'green' | 'purple';
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

const colorConfig = {
  blue: {
    iconBg: 'rgba(59, 130, 246, 0.1)',
    iconColor: '#3B82F6',
    borderColor: 'rgba(59, 130, 246, 0.3)',
  },
  red: {
    iconBg: 'rgba(239, 68, 68, 0.1)',
    iconColor: '#EF4444',
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  green: {
    iconBg: 'rgba(16, 185, 129, 0.1)',
    iconColor: '#10B981',
    borderColor: 'rgba(16, 185, 129, 0.3)',
  },
  purple: {
    iconBg: 'rgba(139, 92, 246, 0.1)',
    iconColor: '#8B5CF6',
    borderColor: 'rgba(139, 92, 246, 0.3)',
  },
};

export const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  subtitle, 
  icon: Icon, 
  color,
  trend 
}) => {
  const colors = colorConfig[color];

  return (
    <Card 
      className="p-6 bg-[#1A1A1A] border border-[#2A2A2A] hover:border-opacity-100 transition-all duration-300 transform hover:-translate-y-1 hover:shadow-lg hover:shadow-black/20"
      style={{
        borderColor: '#2A2A2A'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = colors.borderColor;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = '#2A2A2A';
      }}
    >
      <div className="space-y-4">
        {/* Icon and Trend */}
        <div className="flex items-start justify-between">
          <div 
            className="w-12 h-12 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: colors.iconBg }}
          >
            <Icon className="w-6 h-6" style={{ color: colors.iconColor }} />
          </div>
          
          {trend && (
            <div className={`flex items-center gap-1 text-sm font-semibold ${
              trend.isPositive ? 'text-green-500' : 'text-red-500'
            }`}>
              {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
            </div>
          )}
        </div>

        {/* Value */}
        <div>
          <div className="text-4xl font-bold text-[#F5F5F5] mb-2">
            {value}
          </div>
          <div className="text-sm font-medium text-[#A3A3A3] mb-1">
            {title}
          </div>
          {subtitle && (
            <div className="text-xs text-[#737373]">
              {subtitle}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
