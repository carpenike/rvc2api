import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { useHealthContext } from '@/contexts/health-context';
import { CheckCircleIcon, AlertTriangleIcon, XCircleIcon, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Overall System Status Card - Level 1 of the Information Pyramid
 * Provides immediate at-a-glance system health status.
 * Designed to be readable from across the room on a NOC monitor.
 */
export function OverallSystemStatusCard() {
  const { status, isConnected } = useHealthContext();

  const getStatusConfig = () => {
    if (!isConnected) {
      return {
        icon: XCircleIcon,
        label: 'DISCONNECTED',
        className: 'text-destructive',
        bgClassName: 'bg-destructive/10',
        iconSize: 'h-16 w-16',
      };
    }

    switch (status) {
      case 'critical':
        return {
          icon: XCircleIcon,
          label: 'CRITICAL',
          className: 'text-destructive',
          bgClassName: 'bg-destructive/10',
          iconSize: 'h-16 w-16',
        };
      case 'warning':
        return {
          icon: AlertTriangleIcon,
          label: 'DEGRADED',
          className: 'text-yellow-600 dark:text-yellow-500',
          bgClassName: 'bg-yellow-50 dark:bg-yellow-900/20',
          iconSize: 'h-16 w-16',
        };
      case 'healthy':
        return {
          icon: CheckCircleIcon,
          label: 'HEALTHY',
          className: 'text-green-600 dark:text-green-500',
          bgClassName: 'bg-green-50 dark:bg-green-900/20',
          iconSize: 'h-16 w-16',
        };
      default:
        return {
          icon: Loader2,
          label: 'LOADING',
          className: 'text-muted-foreground',
          bgClassName: 'bg-muted/10',
          iconSize: 'h-16 w-16',
          isLoading: true,
        };
    }
  };

  const statusConfig = getStatusConfig();
  const Icon = statusConfig.icon;

  return (
    <Card className={cn('overflow-hidden', statusConfig.bgClassName)}>
      <CardContent className="flex flex-col items-center justify-center p-6">
        <Icon
          className={cn(
            statusConfig.iconSize,
            statusConfig.className,
            statusConfig.isLoading && 'animate-spin'
          )}
        />
        <h2 className={cn('mt-4 text-2xl font-bold', statusConfig.className)}>
          {statusConfig.label}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          System Status
        </p>
      </CardContent>
    </Card>
  );
}
