/**
 * Trend Chart - Line chart for time-series data
 */
'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card } from '@/components/ui/Card';

interface TrendChartProps {
  title: string;
  data: Array<{
    date: string;
    scans?: number;
    vulnerabilities?: number;
  }>;
  dataKeys: Array<{
    key: string;
    name: string;
    color: string;
  }>;
}

export function TrendChart({ title, data, dataKeys }: TrendChartProps) {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="date" 
            stroke="#6b7280"
            fontSize={12}
          />
          <YAxis stroke="#6b7280" fontSize={12} />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            }}
          />
          <Legend />
          {dataKeys.map((dataKey) => (
            <Line
              key={dataKey.key}
              type="monotone"
              dataKey={dataKey.key}
              name={dataKey.name}
              stroke={dataKey.color}
              strokeWidth={2}
              dot={{ fill: dataKey.color, r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}

