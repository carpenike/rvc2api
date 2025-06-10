/**
 * Advanced Analytics Dashboard
 *
 * Comprehensive analytics dashboard providing performance trends, system insights,
 * historical analysis, and metrics aggregation with interactive visualizations.
 */

import { AppLayout } from "@/components/app-layout"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useState } from "react"
// import { Input } from "@/components/ui/input" // Reserved for future filter functionality
// import { Label } from "@/components/ui/label" // Reserved for future form labels
// import { Separator } from "@/components/ui/separator" // Reserved for layout improvements
import { useAnalyticsDashboard } from "@/hooks/useAnalyticsDashboard"
import type {
  PerformanceAlert,
  SystemInsight,
  HistoricalPattern,
  AnalyticsMetricData
} from "@/api/types/domains"
import {
  IconActivity,
  IconAlertTriangle,
  IconAnalyze,
  IconBrain,
  IconChartBar,
  IconChartLine,
  IconEye,
  IconInfoCircle,
  IconRefresh,
  IconSettings,
  IconTrendingDown,
  IconTrendingUp,
  IconWaveSquare,
} from "@tabler/icons-react"
// Reserved icons for future features:
// IconChartArea, IconClock, IconDashboard, IconFilter

/**
 * Performance Trends Card
 */
function PerformanceTrendsCard() {
  const [timeWindow, setTimeWindow] = useState("24")
  const [resolution, setResolution] = useState("1h")
  const { trends, isLoadingTrends, refreshTrends } = useAnalyticsDashboard({
    timeWindowHours: parseInt(timeWindow),
    resolution
  })

  if (isLoadingTrends) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconChartLine className="h-5 w-5" />
            Performance Trends
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    )
  }

  const trendsData = trends
  const summary = trendsData?.summary || {
    trending_up: 0,
    trending_down: 0,
    stable: 0,
    total_anomalies: 0,
    key_insights: []
  }
  const metrics = trendsData?.metrics || {}
  const alerts = trendsData?.alerts || []

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <IconChartLine className="h-5 w-5" />
              Performance Trends
            </CardTitle>
            <CardDescription>
              System performance analysis over {timeWindow} hours
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Select value={timeWindow} onValueChange={setTimeWindow}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1h</SelectItem>
                <SelectItem value="6">6h</SelectItem>
                <SelectItem value="24">24h</SelectItem>
                <SelectItem value="168">7d</SelectItem>
              </SelectContent>
            </Select>
            <Select value={resolution} onValueChange={setResolution}>
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1m">1m</SelectItem>
                <SelectItem value="5m">5m</SelectItem>
                <SelectItem value="15m">15m</SelectItem>
                <SelectItem value="1h">1h</SelectItem>
                <SelectItem value="6h">6h</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={() => void refreshTrends()}>
              <IconRefresh className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Trends Summary */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold text-green-500">
              {summary.trending_up || 0}
            </div>
            <div className="text-xs text-muted-foreground">Trending Up</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold text-red-500">
              {summary.trending_down || 0}
            </div>
            <div className="text-xs text-muted-foreground">Trending Down</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold text-blue-500">
              {summary.stable || 0}
            </div>
            <div className="text-xs text-muted-foreground">Stable</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold text-yellow-500">
              {summary.total_anomalies || 0}
            </div>
            <div className="text-xs text-muted-foreground">Anomalies</div>
          </div>
        </div>

        {/* Performance Alerts */}
        {alerts.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-medium mb-2">Performance Alerts</h4>
            <div className="space-y-2">
              {alerts.map((alert: PerformanceAlert, index: number) => (
                <Alert key={index} variant={alert.severity === "high" ? "destructive" : "default"}>
                  <IconAlertTriangle className="h-4 w-4" />
                  <AlertTitle>{alert.type.replace(/_/g, " ").toUpperCase()}</AlertTitle>
                  <AlertDescription>
                    {alert.message}
                    {alert.recommendation && (
                      <div className="mt-1 text-sm">
                        <strong>Recommendation:</strong> {alert.recommendation}
                      </div>
                    )}
                  </AlertDescription>
                </Alert>
              ))}
            </div>
          </div>
        )}

        {/* Metrics List */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium">Metric Details</h4>
          {Object.entries(metrics).map(([metricName, metricData]: [string, AnalyticsMetricData]) => (
            <div key={metricName} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h5 className="font-medium">{metricName.replace(/_/g, " ").toUpperCase()}</h5>
                <div className="flex items-center gap-2">
                  {metricData.trend_direction === "up" && (
                    <IconTrendingUp className="h-4 w-4 text-green-500" />
                  )}
                  {metricData.trend_direction === "down" && (
                    <IconTrendingDown className="h-4 w-4 text-red-500" />
                  )}
                  {metricData.trend_direction === "stable" && (
                    <IconWaveSquare className="h-4 w-4 text-blue-500" />
                  )}
                  <Badge variant="outline">
                    {metricData.change_percent > 0 ? "+" : ""}{metricData.change_percent}%
                  </Badge>
                </div>
              </div>
              <div className="text-sm text-muted-foreground">
                Data points: {metricData.data_points?.length || 0} |
                Anomalies: {metricData.anomaly_count || 0} |
                Quality: {metricData.data_quality || "unknown"}
              </div>
              {metricData.anomaly_count > 0 && (
                <Progress
                  value={(metricData.anomaly_count / (metricData.data_points?.length || 1)) * 100}
                  className="mt-2"
                />
              )}
            </div>
          ))}
        </div>

        {/* Key Insights */}
        {summary.key_insights && summary.key_insights.length > 0 && (
          <div className="mt-6">
            <h4 className="text-sm font-medium mb-2">Key Insights</h4>
            <div className="space-y-2">
              {summary.key_insights.map((insight: string, index: number) => (
                <div key={index} className="flex items-start gap-2 p-3 bg-background/50 rounded-lg">
                  <IconEye className="h-4 w-4 mt-0.5 text-blue-500" />
                  <span className="text-sm">{insight}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * System Insights Card
 */
function SystemInsightsCard() {
  const [minSeverity, setMinSeverity] = useState("low")
  const [categories] = useState<string[]>([])
  // const [, setCategories] = useState<string[]>([]) // Reserved for future category filtering
  const { insights, isLoadingInsights, refreshInsights } = useAnalyticsDashboard({
    minSeverity,
    categories
  })

  if (isLoadingInsights) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconBrain className="h-5 w-5" />
            System Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    )
  }

  const insightsData = insights
  const insightsList = insightsData?.insights || []
  const summary = insightsData?.summary || {
    total_count: 0,
    avg_confidence: 0,
    avg_impact: 0
  }
  const severityDistribution = insightsData?.severity_distribution || {}

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <IconBrain className="h-5 w-5" />
              System Insights
            </CardTitle>
            <CardDescription>
              AI-powered system analysis and recommendations
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Select value={minSeverity} onValueChange={setMinSeverity}>
              <SelectTrigger className="w-28">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low+</SelectItem>
                <SelectItem value="medium">Medium+</SelectItem>
                <SelectItem value="high">High+</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={() => void refreshInsights()}>
              <IconRefresh className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Insights Summary */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold">
              {summary.total_count || 0}
            </div>
            <div className="text-xs text-muted-foreground">Total Insights</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold">
              {Math.round((summary.avg_confidence || 0) * 100)}%
            </div>
            <div className="text-xs text-muted-foreground">Avg Confidence</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold">
              {Math.round((summary.avg_impact || 0) * 100)}%
            </div>
            <div className="text-xs text-muted-foreground">Avg Impact</div>
          </div>
        </div>

        {/* Severity Distribution */}
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-2">Severity Distribution</h4>
          <div className="grid grid-cols-4 gap-2">
            {Object.entries(severityDistribution).map(([severity, count]: [string, number]) => (
              <div key={severity} className="text-center p-2 bg-background/30 rounded">
                <div className="font-medium">{count}</div>
                <div className="text-xs text-muted-foreground capitalize">{severity}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Insights List */}
        {insightsList.length > 0 ? (
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Recent Insights</h4>
            {insightsList.slice(0, 10).map((insight: SystemInsight, index: number) => (
              <div key={insight.insight_id || index} className="border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h5 className="font-medium">{insight.title}</h5>
                    <p className="text-sm text-muted-foreground mt-1">
                      {insight.description}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <Badge
                      variant={insight.severity === "critical" ? "destructive" :
                               insight.severity === "high" ? "destructive" :
                               insight.severity === "medium" ? "default" : "secondary"}
                    >
                      {insight.severity}
                    </Badge>
                    <Badge variant="outline">
                      {Math.round(insight.confidence * 100)}%
                    </Badge>
                  </div>
                </div>

                {insight.recommendations && insight.recommendations.length > 0 && (
                  <div className="mt-3">
                    <h6 className="text-xs font-medium text-muted-foreground mb-1">RECOMMENDATIONS</h6>
                    <ul className="text-sm space-y-1">
                      {insight.recommendations.map((rec: string, recIndex: number) => (
                        <li key={recIndex} className="flex items-start gap-2">
                          <span className="text-muted-foreground">•</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                  <span>Category: {insight.category}</span>
                  <span>Impact: {Math.round(insight.impact_score * 100)}%</span>
                  <span>Created: {new Date(insight.created_at * 1000).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <IconInfoCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No Insights Available</h3>
            <p className="text-muted-foreground">
              System insights will appear here as data is collected and analyzed.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Historical Analysis Card
 */
function HistoricalAnalysisCard() {
  const [analysisType, setAnalysisType] = useState("pattern_detection")
  const [timeWindow, setTimeWindow] = useState("168")
  const { historical, isLoadingHistorical, refreshHistorical } = useAnalyticsDashboard({
    analysisType,
    timeWindowHours: parseInt(timeWindow)
  })

  if (isLoadingHistorical) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconAnalyze className="h-5 w-5" />
            Historical Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    )
  }

  const historicalData = historical
  const patterns = historicalData?.patterns || []
  const anomalies = historicalData?.anomalies || []
  const correlations = historicalData?.correlations || []
  const predictions = historicalData?.predictions || []
  const summary = historicalData?.summary || {
    patterns_found: 0,
    anomalies_detected: 0,
    correlations_found: 0,
    predictions_generated: 0
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <IconAnalyze className="h-5 w-5" />
              Historical Analysis
            </CardTitle>
            <CardDescription>
              Pattern detection and predictive analytics
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Select value={analysisType} onValueChange={setAnalysisType}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pattern_detection">Patterns</SelectItem>
                <SelectItem value="anomaly_detection">Anomalies</SelectItem>
                <SelectItem value="correlation">Correlations</SelectItem>
                <SelectItem value="all">All Analysis</SelectItem>
              </SelectContent>
            </Select>
            <Select value={timeWindow} onValueChange={setTimeWindow}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="168">7d</SelectItem>
                <SelectItem value="336">14d</SelectItem>
                <SelectItem value="720">30d</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={() => void refreshHistorical()}>
              <IconRefresh className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Analysis Summary */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold text-blue-500">
              {summary.patterns_found || 0}
            </div>
            <div className="text-xs text-muted-foreground">Patterns</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold text-yellow-500">
              {summary.anomalies_detected || 0}
            </div>
            <div className="text-xs text-muted-foreground">Anomalies</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold text-purple-500">
              {summary.correlations_found || 0}
            </div>
            <div className="text-xs text-muted-foreground">Correlations</div>
          </div>
          <div className="text-center p-3 bg-background/50 rounded-lg">
            <div className="text-2xl font-semibold text-green-500">
              {summary.predictions_generated || 0}
            </div>
            <div className="text-xs text-muted-foreground">Predictions</div>
          </div>
        </div>

        {/* Analysis Results */}
        <Tabs defaultValue="patterns">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="patterns">Patterns</TabsTrigger>
            <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
            <TabsTrigger value="correlations">Correlations</TabsTrigger>
            <TabsTrigger value="predictions">Predictions</TabsTrigger>
          </TabsList>

          <TabsContent value="patterns" className="space-y-4">
            {patterns.length > 0 ? (
              patterns.map((pattern: HistoricalPattern, index: number) => (
                <div key={pattern.pattern_id || index} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="font-medium">{pattern.description}</h5>
                    <Badge variant="outline">
                      {Math.round(pattern.confidence * 100)}% confidence
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Type: {pattern.pattern_type} |
                    {pattern.frequency && ` Frequency: ${pattern.frequency} |`}
                    {pattern.correlation_factors.length > 0 && ` Factors: ${pattern.correlation_factors.join(", ")}`}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No patterns detected in the selected time window.
              </div>
            )}
          </TabsContent>

          <TabsContent value="anomalies" className="space-y-4">
            {anomalies.length > 0 ? (
              anomalies.map((_anomaly: unknown, index: number) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="text-sm">Anomaly data would be displayed here</div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No anomalies detected in the selected time window.
              </div>
            )}
          </TabsContent>

          <TabsContent value="correlations" className="space-y-4">
            {correlations.length > 0 ? (
              correlations.map((_correlation: unknown, index: number) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="text-sm">Correlation data would be displayed here</div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No correlations found in the selected time window.
              </div>
            )}
          </TabsContent>

          <TabsContent value="predictions" className="space-y-4">
            {predictions.length > 0 ? (
              predictions.map((_prediction: unknown, index: number) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="text-sm">Prediction data would be displayed here</div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No predictions generated for the selected time window.
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

/**
 * Metrics Aggregation Card
 */
function MetricsAggregationCard() {
  const { aggregation, isLoadingAggregation, refreshAggregation } = useAnalyticsDashboard()

  if (isLoadingAggregation) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconChartBar className="h-5 w-5" />
            Metrics Aggregation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-48 w-full" />
        </CardContent>
      </Card>
    )
  }

  const aggregationData = aggregation
  const windows = aggregationData?.windows || {}
  const kpis = aggregationData?.kpis || {}
  const recommendations = aggregationData?.recommendations || []

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <IconChartBar className="h-5 w-5" />
              Metrics Aggregation
            </CardTitle>
            <CardDescription>
              Comprehensive metrics reporting and KPIs
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => void refreshAggregation()}>
            <IconRefresh className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* KPI Overview */}
        <div className="mb-6">
          <h4 className="text-sm font-medium mb-4">Key Performance Indicators</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(kpis).slice(0, 8).map(([kpi, value]: [string, number | string]) => (
              <div key={kpi} className="text-center p-3 bg-background/50 rounded-lg">
                <div className="text-xl font-semibold">
                  {typeof value === "number" ? Math.round(value * 100) / 100 : value}
                </div>
                <div className="text-xs text-muted-foreground">
                  {kpi.replace(/_/g, " ").toUpperCase()}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Time Windows */}
        {Object.keys(windows).length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-medium mb-4">Aggregation Windows</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(windows).map(([window, _data]: [string, unknown]) => (
                <div key={window} className="border rounded-lg p-4">
                  <h5 className="font-medium mb-2">{window.toUpperCase()}</h5>
                  <div className="text-sm text-muted-foreground">
                    Window data would be displayed here
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Optimization Recommendations */}
        {recommendations.length > 0 && (
          <div>
            <h4 className="text-sm font-medium mb-4">Optimization Recommendations</h4>
            <div className="space-y-3">
              {recommendations.slice(0, 5).map((_rec: unknown, index: number) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="text-sm">
                    Recommendation {index + 1} would be displayed here
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {Object.keys(windows).length === 0 && Object.keys(kpis).length === 0 && (
          <div className="text-center py-8">
            <IconChartBar className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">No Metrics Data</h3>
            <p className="text-muted-foreground">
              Metrics aggregation will appear here as data is collected over time.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Main Analytics Dashboard Page
 */
export default function AnalyticsDashboardPage() {
  const { status, refreshAll } = useAnalyticsDashboard()

  return (
    <AppLayout pageTitle="Analytics Dashboard">
      <div className="flex-1 space-y-6 p-4 pt-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
            <p className="text-muted-foreground">
              Comprehensive performance insights and intelligent system analytics
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => void refreshAll()} variant="outline" className="gap-2">
              <IconRefresh className="h-4 w-4" />
              Refresh All
            </Button>
            <Button variant="outline" className="gap-2">
              <IconSettings className="h-4 w-4" />
              Configure
            </Button>
          </div>
        </div>

        {/* Service Status */}
        {Boolean(status) && (
          <Alert>
            <IconActivity className="h-4 w-4" />
            <AlertTitle>Analytics Service Status</AlertTitle>
            <AlertDescription>
              {(() => {
                const statusData = status
                return (
                  <>
                    Service: {statusData?.service_status || 'Unknown'} |
                    Metrics Tracked: {statusData?.metrics_tracked || 0} |
                    Insights: {statusData?.insights_cached || 0} |
                    Patterns: {statusData?.patterns_detected || 0}
                  </>
                )
              })()}
            </AlertDescription>
          </Alert>
        )}

        {/* Main Content Tabs */}
        <Tabs defaultValue="trends" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="trends" className="gap-2">
              <IconChartLine className="h-4 w-4" />
              Performance Trends
            </TabsTrigger>
            <TabsTrigger value="insights" className="gap-2">
              <IconBrain className="h-4 w-4" />
              System Insights
            </TabsTrigger>
            <TabsTrigger value="historical" className="gap-2">
              <IconAnalyze className="h-4 w-4" />
              Historical Analysis
            </TabsTrigger>
            <TabsTrigger value="aggregation" className="gap-2">
              <IconChartBar className="h-4 w-4" />
              Metrics & KPIs
            </TabsTrigger>
          </TabsList>

          <TabsContent value="trends">
            <PerformanceTrendsCard />
          </TabsContent>

          <TabsContent value="insights">
            <SystemInsightsCard />
          </TabsContent>

          <TabsContent value="historical">
            <HistoricalAnalysisCard />
          </TabsContent>

          <TabsContent value="aggregation">
            <MetricsAggregationCard />
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  )
}
