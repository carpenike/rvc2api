import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { IconActivity } from '@tabler/icons-react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

// Simple inline sparkline component
function Sparkline({ data, className }: { data: number[]; className?: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const width = 80;
  const height = 20;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} className={className}>
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

interface Metric {
  label: string;
  value: string;
  trend: 'up' | 'down' | 'stable';
  sparklineData: number[];
  status: 'good' | 'warning' | 'critical';
}

/**
 * Performance Metrics Summary Card - Level 2 of the Information Pyramid
 * Shows key performance indicators with sparklines for trend visualization.
 */
export function PerformanceMetricsSummaryCard() {
  // In a real implementation, this would come from your performance monitoring hooks
  const metrics: Metric[] = [
    {
      label: 'CPU Usage',
      value: '42%',
      trend: 'stable',
      sparklineData: [40, 42, 41, 43, 42, 44, 42, 41, 42],
      status: 'good',
    },
    {
      label: 'Memory',
      value: '68%',
      trend: 'up',
      sparklineData: [60, 62, 63, 65, 66, 67, 68, 68, 68],
      status: 'warning',
    },
    {
      label: 'Latency',
      value: '12ms',
      trend: 'down',
      sparklineData: [15, 14, 13, 14, 13, 12, 12, 11, 12],
      status: 'good',
    },
  ];

  const getTrendIcon = (trend: Metric['trend']) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-3 w-3" />;
      case 'down':
        return <TrendingDown className="h-3 w-3" />;
      default:
        return <Minus className="h-3 w-3" />;
    }
  };

  const getStatusColor = (status: Metric['status']) => {
    switch (status) {
      case 'critical':
        return 'text-destructive';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-500';
      default:
        return 'text-green-600 dark:text-green-500';
    }
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <IconActivity className="h-5 w-5" />
          <span>Performance</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {metrics.map((metric) => (
          <div key={metric.label} className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{metric.label}</span>
              <div className="flex items-center gap-1">
                {getTrendIcon(metric.trend)}
                <span className={cn('text-sm font-semibold', getStatusColor(metric.status))}>
                  {metric.value}
                </span>
              </div>
            </div>
            <div className="flex justify-end">
              <Sparkline
                data={metric.sparklineData}
                className={getStatusColor(metric.status)}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
