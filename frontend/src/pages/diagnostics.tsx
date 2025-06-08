/**
 * Advanced Diagnostics Dashboard
 *
 * Comprehensive diagnostic interface providing system health monitoring,
 * DTC management, fault correlation analysis, and predictive maintenance.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import {
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  Wrench,
  Activity,
  Shield,
  AlertTriangle,
  Search,
  RefreshCw
} from 'lucide-react';

import {
  fetchSystemHealth,
  fetchActiveDTCs,
  fetchFaultCorrelations,
  fetchMaintenancePredictions,
  resolveDTC
} from '@/api/endpoints';
import type {
  DTCFilters,
  DiagnosticTroubleCode
} from '@/api/types';

// Helper function to get health status color and icon
const getHealthIndicator = (score: number, status: string) => {
  if (status === 'critical' || score < 0.5) {
    return {
      color: 'text-red-500',
      bgColor: 'bg-red-50 border-red-200',
      icon: AlertCircle,
      label: 'Critical'
    };
  } else if (status === 'warning' || score < 0.8) {
    return {
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-50 border-yellow-200',
      icon: AlertTriangle,
      label: 'Warning'
    };
  } else {
    return {
      color: 'text-green-500',
      bgColor: 'bg-green-50 border-green-200',
      icon: CheckCircle,
      label: 'Healthy'
    };
  }
};

// Helper function to get severity badge variant
const getSeverityVariant = (severity: string) => {
  switch (severity) {
    case 'critical': return 'destructive';
    case 'high': return 'destructive';
    case 'medium': return 'secondary';
    case 'low': return 'outline';
    default: return 'outline';
  }
};

// System Health Overview Component
const SystemHealthOverview: React.FC = () => {
  const { data: healthData, isLoading, refetch } = useQuery({
    queryKey: ['diagnostics', 'system-health'],
    queryFn: () => fetchSystemHealth(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="animate-pulse bg-gray-200 h-4 rounded"></div>
            <div className="animate-pulse bg-gray-200 h-20 rounded"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!healthData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Unable to load system health data</p>
        </CardContent>
      </Card>
    );
  }

  const healthIndicator = getHealthIndicator(healthData.overall_health, healthData.status);
  const HealthIcon = healthIndicator.icon;

  return (
    <Card className={healthIndicator.bgColor}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Health
          </div>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </CardTitle>
        <CardDescription>
          Overall system health and active issues
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Overall Health Score */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-3 mb-2">
              <HealthIcon className={`h-8 w-8 ${healthIndicator.color}`} />
              <div className="text-4xl font-bold">
                {Math.round(healthData.overall_health * 100)}%
              </div>
            </div>
            <Progress
              value={healthData.overall_health * 100}
              className="w-full h-2"
            />
            <p className="text-sm text-muted-foreground mt-2">
              System Health Score
            </p>
          </div>

          <Separator />

          {/* System Scores Breakdown */}
          <div>
            <h4 className="text-sm font-medium mb-3">Subsystem Health</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(healthData.system_scores).map(([system, score]) => (
                <div key={system} className="flex items-center justify-between p-2 rounded border">
                  <span className="text-sm capitalize">{system.replace('_', ' ')}</span>
                  <div className="flex items-center gap-2">
                    <Progress value={score * 100} className="w-16 h-1" />
                    <span className="text-xs font-medium w-8">
                      {Math.round(score * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active DTCs Summary */}
          {healthData.active_dtcs > 0 && (
            <>
              <Separator />
              <div className="flex items-center justify-between p-3 rounded border border-orange-200 bg-orange-50">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-orange-500" />
                  <span className="text-sm font-medium">Active Issues</span>
                </div>
                <Badge variant="secondary">{healthData.active_dtcs} DTCs</Badge>
              </div>
            </>
          )}

          {/* Recommendations */}
          {healthData.recommendations.length > 0 && (
            <>
              <Separator />
              <div>
                <h4 className="text-sm font-medium mb-2">Recommendations</h4>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  {healthData.recommendations.slice(0, 3).map((rec, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <div className="h-1.5 w-1.5 rounded-full bg-blue-500 mt-2 flex-shrink-0" />
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// DTC Management Component
const DTCManager: React.FC = () => {
  const [filters, setFilters] = useState<DTCFilters>({});
  const [searchTerm, setSearchTerm] = useState('');

  const { data: dtcData, isLoading, refetch } = useQuery({
    queryKey: ['diagnostics', 'active-dtcs', filters],
    queryFn: () => fetchActiveDTCs(filters),
    refetchInterval: 15000, // Refresh every 15 seconds
  });

  const handleResolveDTC = async (dtc: DiagnosticTroubleCode) => {
    try {
      await resolveDTC(dtc.protocol, parseInt(dtc.code), dtc.source_address);
      refetch(); // Refresh the list after resolution
    } catch (error) {
      console.error('Failed to resolve DTC:', error);
      // TODO: Add toast notification for error
    }
  };

  const filteredDTCs = dtcData?.dtcs.filter(dtc =>
    !searchTerm ||
    dtc.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dtc.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    dtc.system_type.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Diagnostic Trouble Codes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Diagnostic Trouble Codes
          </div>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </CardTitle>
        <CardDescription>
          Active diagnostic trouble codes across all protocols
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Summary Stats */}
          {dtcData && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 rounded border">
                <div className="text-2xl font-bold">{dtcData.total_count}</div>
                <div className="text-xs text-muted-foreground">Total DTCs</div>
              </div>
              <div className="text-center p-3 rounded border">
                <div className="text-2xl font-bold text-red-500">{dtcData.active_count}</div>
                <div className="text-xs text-muted-foreground">Active</div>
              </div>
              <div className="text-center p-3 rounded border">
                <div className="text-2xl font-bold text-orange-500">
                  {dtcData.by_severity.critical || 0}
                </div>
                <div className="text-xs text-muted-foreground">Critical</div>
              </div>
              <div className="text-center p-3 rounded border">
                <div className="text-2xl font-bold text-blue-500">
                  {Object.keys(dtcData.by_protocol).length}
                </div>
                <div className="text-xs text-muted-foreground">Protocols</div>
              </div>
            </div>
          )}

          {/* Filters and Search */}
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search DTCs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filters.severity || ""} onValueChange={(value) =>
              setFilters(prev => ({ ...prev, severity: value || undefined }))
            }>
              <SelectTrigger className="w-full sm:w-32">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Severities</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filters.protocol || ""} onValueChange={(value) =>
              setFilters(prev => ({ ...prev, protocol: value || undefined }))
            }>
              <SelectTrigger className="w-full sm:w-32">
                <SelectValue placeholder="Protocol" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Protocols</SelectItem>
                <SelectItem value="rvc">RV-C</SelectItem>
                <SelectItem value="j1939">J1939</SelectItem>
                <SelectItem value="firefly">Firefly</SelectItem>
                <SelectItem value="spartan_k2">Spartan K2</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* DTC Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Protocol</TableHead>
                  <TableHead>System</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Count</TableHead>
                  <TableHead>Last Seen</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDTCs.length ? (
                  filteredDTCs.map((dtc) => (
                    <TableRow key={dtc.id}>
                      <TableCell className="font-mono">{dtc.code}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="uppercase">
                          {dtc.protocol}
                        </Badge>
                      </TableCell>
                      <TableCell className="capitalize">
                        {dtc.system_type.replace('_', ' ')}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getSeverityVariant(dtc.severity)}>
                          {dtc.severity}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {dtc.description}
                      </TableCell>
                      <TableCell>{dtc.count}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(dtc.last_seen).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        {!dtc.resolved && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleResolveDTC(dtc)}
                            className="text-xs"
                          >
                            Resolve
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={8} className="h-24 text-center">
                      No DTCs found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Fault Correlation Component
const FaultCorrelationView: React.FC = () => {
  const { data: correlations, isLoading } = useQuery({
    queryKey: ['diagnostics', 'fault-correlations'],
    queryFn: () => fetchFaultCorrelations(),
    refetchInterval: 60000, // Refresh every minute
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Fault Correlations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Fault Correlations
        </CardTitle>
        <CardDescription>
          Related faults and potential root causes
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {correlations && correlations.length > 0 ? (
            correlations.map((correlation) => (
              <div key={correlation.correlation_id} className="p-4 rounded border">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="font-mono">
                      {correlation.primary_dtc}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {correlation.temporal_relationship}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">
                      {Math.round(correlation.confidence * 100)}% confidence
                    </div>
                    <Progress value={correlation.confidence * 100} className="w-20 h-1 mt-1" />
                  </div>
                </div>

                <div className="text-sm">
                  <p className="font-medium mb-1">Related DTCs:</p>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {correlation.related_dtcs.map((dtc) => (
                      <Badge key={dtc} variant="secondary" className="font-mono text-xs">
                        {dtc}
                      </Badge>
                    ))}
                  </div>

                  <p className="text-muted-foreground">
                    <span className="font-medium">Suggested cause:</span> {correlation.suggested_cause}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No fault correlations detected
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Maintenance Predictions Component
const MaintenancePredictions: React.FC = () => {
  const { data: predictions, isLoading } = useQuery({
    queryKey: ['diagnostics', 'maintenance-predictions'],
    queryFn: () => fetchMaintenancePredictions(),
    refetchInterval: 300000, // Refresh every 5 minutes
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wrench className="h-5 w-5" />
            Maintenance Predictions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const sortedPredictions = predictions?.sort((a, b) => {
    const urgencyOrder = { critical: 4, high: 3, medium: 2, low: 1 };
    return urgencyOrder[b.urgency] - urgencyOrder[a.urgency];
  }) || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wrench className="h-5 w-5" />
          Maintenance Predictions
        </CardTitle>
        <CardDescription>
          Predictive maintenance recommendations based on system analysis
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {sortedPredictions.length > 0 ? (
            sortedPredictions.map((prediction, index) => (
              <div key={index} className="p-4 rounded border">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-medium">{prediction.component_name}</h4>
                    <p className="text-sm text-muted-foreground capitalize">
                      {prediction.system_type.replace('_', ' ')}
                    </p>
                  </div>
                  <div className="text-right">
                    <Badge variant={getSeverityVariant(prediction.urgency)}>
                      {prediction.urgency}
                    </Badge>
                    <div className="text-xs text-muted-foreground mt-1">
                      ${prediction.estimated_cost.toLocaleString()}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Failure Probability</span>
                    <span className="font-medium">
                      {Math.round(prediction.failure_probability * 100)}%
                    </span>
                  </div>
                  <Progress value={prediction.failure_probability * 100} className="h-2" />

                  <div className="flex items-center justify-between text-sm">
                    <span>Prediction Confidence</span>
                    <span className="font-medium">
                      {Math.round(prediction.confidence * 100)}%
                    </span>
                  </div>
                  <Progress value={prediction.confidence * 100} className="h-1" />
                </div>

                <div className="mt-3 text-sm">
                  <p className="text-muted-foreground mb-1">
                    <Clock className="inline h-3 w-3 mr-1" />
                    Predicted failure: {new Date(prediction.predicted_failure_date).toLocaleDateString()}
                  </p>
                  <p className="font-medium">{prediction.recommended_action}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No maintenance predictions available
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Main Diagnostics Dashboard Component
export default function DiagnosticsPage() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Diagnostics Dashboard</h1>
          <p className="text-muted-foreground">
            Advanced system health monitoring and diagnostic trouble code management
          </p>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="dtcs">Trouble Codes</TabsTrigger>
          <TabsTrigger value="correlations">Correlations</TabsTrigger>
          <TabsTrigger value="maintenance">Maintenance</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SystemHealthOverview />
            <DTCManager />
          </div>
        </TabsContent>

        <TabsContent value="dtcs" className="space-y-6">
          <DTCManager />
        </TabsContent>

        <TabsContent value="correlations" className="space-y-6">
          <FaultCorrelationView />
        </TabsContent>

        <TabsContent value="maintenance" className="space-y-6">
          <MaintenancePredictions />
        </TabsContent>
      </Tabs>
    </div>
  );
}
