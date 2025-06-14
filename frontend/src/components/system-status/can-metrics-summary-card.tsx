import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { IconActivity, IconTrendingUp, IconTrendingDown } from '@tabler/icons-react';
import { TrendingUp, TrendingDown, Minus, ChevronRight } from 'lucide-react';
import { Area, AreaChart, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { cn } from '@/lib/utils';

// Simple sparkline component (reuse from PerformanceMetricsSummaryCard)
function Sparkline({ data, className, color = 'currentColor' }: { data: number[]; className?: string; color?: string }) {
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
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * CAN Metrics Summary Card - Compact visualization for the main dashboard
 * Shows key metrics with sparklines and provides drill-down to full chart
 */
export function CANMetricsSummaryCard() {
  const [isChartOpen, setIsChartOpen] = useState(false);

  // In a real implementation, this would come from useCANMetrics hook
  const generateMetricsData = () => {
    const data = [];
    const now = new Date();
    for (let i = 29; i >= 0; i--) {
      const date = new Date(now);
      date.setMinutes(date.getMinutes() - i * 2);
      data.push({
        timestamp: date.toISOString(),
        messageRate: Math.floor(Math.random() * 50) + 75,
        errorRate: Math.random() * 3,
        busLoad: Math.random() * 40 + 30,
      });
    }
    return data;
  };

  const metricsData = generateMetricsData();
  const latestMetrics = metricsData[metricsData.length - 1];

  // Extract data for sparklines
  const messageRateData = metricsData.map(d => d.messageRate);
  const errorRateData = metricsData.map(d => d.errorRate);
  const busLoadData = metricsData.map(d => d.busLoad);

  // Calculate trends
  const calculateTrend = (data: number[]) => {
    if (data.length < 2) return 'stable';
    const recent = data.slice(-5);
    const older = data.slice(-10, -5);
    const recentAvg = recent.reduce((a, b) => a + b) / recent.length;
    const olderAvg = older.reduce((a, b) => a + b) / older.length;
    const change = ((recentAvg - olderAvg) / olderAvg) * 100;
    if (change > 5) return 'up';
    if (change < -5) return 'down';
    return 'stable';
  };

  const metrics = latestMetrics ? [
    {
      label: 'Message Rate',
      value: `${latestMetrics.messageRate} msg/s`,
      trend: calculateTrend(messageRateData),
      sparklineData: messageRateData.slice(-10),
      color: 'text-blue-600',
    },
    {
      label: 'Error Rate',
      value: `${latestMetrics.errorRate.toFixed(2)}%`,
      trend: calculateTrend(errorRateData),
      sparklineData: errorRateData.slice(-10),
      color: latestMetrics.errorRate > 2 ? 'text-red-600' : 'text-green-600',
    },
    {
      label: 'Bus Load',
      value: `${latestMetrics.busLoad.toFixed(0)}%`,
      trend: calculateTrend(busLoadData),
      sparklineData: busLoadData.slice(-10),
      color: latestMetrics.busLoad > 70 ? 'text-yellow-600' : 'text-green-600',
    },
  ] : [];

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-3 w-3" />;
      case 'down':
        return <TrendingDown className="h-3 w-3" />;
      default:
        return <Minus className="h-3 w-3" />;
    }
  };

  return (
    <>
      <Card
        className="cursor-pointer hover:shadow-md transition-shadow"
        onClick={() => setIsChartOpen(true)}
      >
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <IconActivity className="h-5 w-5" />
              <span>CAN Metrics</span>
            </div>
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {metrics.map((metric) => (
            <div key={metric.label} className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">{metric.label}</span>
                <div className="flex items-center gap-1">
                  {getTrendIcon(metric.trend)}
                  <span className={cn('text-sm font-semibold', metric.color)}>
                    {metric.value}
                  </span>
                </div>
              </div>
              <div className="flex justify-end">
                <Sparkline
                  data={metric.sparklineData}
                  className={metric.color}
                />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Dialog open={isChartOpen} onOpenChange={setIsChartOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>CAN Bus Metrics - Detailed View</DialogTitle>
          </DialogHeader>
          <div className="space-y-6 mt-4">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metricsData}>
                  <defs>
                    <linearGradient id="messageRate" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="errorRate" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                    className="text-xs"
                  />
                  <YAxis className="text-xs" />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))'
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="messageRate"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#messageRate)"
                    name="Message Rate (msg/s)"
                  />
                  <Area
                    type="monotone"
                    dataKey="errorRate"
                    stroke="#ef4444"
                    fillOpacity={1}
                    fill="url(#errorRate)"
                    name="Error Rate (%)"
                    yAxisId="right"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex gap-4 justify-center">
              <Badge variant="outline" className="gap-2">
                <div className="w-3 h-3 bg-blue-600 rounded" />
                Message Rate
              </Badge>
              <Badge variant="outline" className="gap-2">
                <div className="w-3 h-3 bg-red-600 rounded" />
                Error Rate
              </Badge>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
