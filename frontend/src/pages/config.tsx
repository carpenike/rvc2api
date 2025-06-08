/**
 * Configuration Management Page
 *
 * Provides comprehensive configuration management interface for CoachIQ system
 * with multi-protocol support, feature flag management, and real-time validation.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import {
  AlertTriangle,
  CheckCircle,
  Settings,
  Network,
  Shield,
  Database,
  Monitor,
  Zap,
  RefreshCw,
  Eye,
  Info
} from 'lucide-react';
import {
  fetchSystemSettings,
  fetchFeatureManagement,
  fetchCANInterfaceMappings,
  fetchCoachConfiguration,
  fetchConfigurationSystemStatus,
  validateConfiguration,
  enableFeature,
  disableFeature
} from '@/api/endpoints';
import type {
  SystemSettings,
  FeatureManagementResponse,
  CANInterfaceMapping,
  CoachConfiguration,
  FeatureFlag
} from '@/api/types';

export default function ConfigurationPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [validationResults, setValidationResults] = useState<Record<string, unknown>>({});
  const queryClient = useQueryClient();

  // Data queries
  const { data: systemSettings, isLoading: settingsLoading, error: settingsError } = useQuery({
    queryKey: ['systemSettings'],
    queryFn: fetchSystemSettings,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: featureManagement, isLoading: featuresLoading } = useQuery({
    queryKey: ['featureManagement'],
    queryFn: fetchFeatureManagement,
    refetchInterval: 15000,
  });

  const { data: canInterfaces, isLoading: interfacesLoading } = useQuery({
    queryKey: ['canInterfaceMappings'],
    queryFn: fetchCANInterfaceMappings,
    refetchInterval: 15000,
  });

  const { data: coachConfig, isLoading: coachLoading } = useQuery({
    queryKey: ['coachConfiguration'],
    queryFn: fetchCoachConfiguration,
  });

  const { data: systemStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['configurationSystemStatus'],
    queryFn: fetchConfigurationSystemStatus,
    refetchInterval: 10000, // Frequent updates for system status
  });

  // Mutations
  const validateConfigMutation = useMutation({
    mutationFn: validateConfiguration,
    onSuccess: (result, variables) => {
      setValidationResults(prev => ({
        ...prev,
        [variables || 'all']: result
      }));
    },
  });

  const updateFeatureMutation = useMutation({
    mutationFn: ({ featureName, enabled }: { featureName: string; enabled: boolean }) =>
      enabled ? enableFeature(featureName) : disableFeature(featureName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['featureManagement'] });
    },
  });

  // Helper functions
  const handleFeatureToggle = (featureName: string, enabled: boolean) => {
    updateFeatureMutation.mutate({ featureName, enabled });
  };

  const handleValidation = (section?: string) => {
    validateConfigMutation.mutate(section);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
      case 'active':
      case 'enabled':
      case 'valid':
        return 'text-green-600';
      case 'warning':
      case 'inactive':
        return 'text-yellow-600';
      case 'error':
      case 'invalid':
      case 'disabled':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
      case 'active':
      case 'enabled':
      case 'valid':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'warning':
      case 'inactive':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'error':
      case 'invalid':
      case 'disabled':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Info className="h-4 w-4 text-gray-600" />;
    }
  };

  if (settingsLoading || statusLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-lg">Loading configuration...</span>
        </div>
      </div>
    );
  }

  if (settingsError) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Configuration Error</AlertTitle>
          <AlertDescription>
            Failed to load system configuration. Please check your connection and try again.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Configuration Management</h1>
          <p className="text-muted-foreground">
            Manage system settings, protocols, and features for your CoachIQ system
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleValidation()}
            disabled={validateConfigMutation.isPending}
          >
            {validateConfigMutation.isPending ? (
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Eye className="h-4 w-4 mr-2" />
            )}
            Validate All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => queryClient.invalidateQueries()}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Status Overview */}
      {systemStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Monitor className="h-5 w-5 mr-2" />
              System Status
            </CardTitle>
            <CardDescription>
              Current system operational status and health indicators
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center space-x-2">
                {getStatusIcon(systemStatus.server_status)}
                <span className={`font-medium ${getStatusColor(systemStatus.server_status)}`}>
                  Server: {systemStatus.server_status}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                {getStatusIcon(systemStatus.validation_status)}
                <span className={`font-medium ${getStatusColor(systemStatus.validation_status)}`}>
                  Config: {systemStatus.validation_status}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant={Object.values(systemStatus.can_interfaces_status).some(s => s === 'active') ? 'default' : 'secondary'}>
                  CAN: {Object.values(systemStatus.can_interfaces_status).filter(s => s === 'active').length} active
                </Badge>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant={Object.values(systemStatus.protocol_status).some(s => s === 'active') ? 'default' : 'secondary'}>
                  Protocols: {Object.values(systemStatus.protocol_status).filter(s => s === 'active').length} active
                </Badge>
              </div>
            </div>
            {systemStatus.pending_restarts.length > 0 && (
              <Alert className="mt-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Restart Required</AlertTitle>
                <AlertDescription>
                  Configuration changes require restart for: {systemStatus.pending_restarts.join(', ')}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Configuration Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="features">Features</TabsTrigger>
          <TabsTrigger value="protocols">Protocols</TabsTrigger>
          <TabsTrigger value="interfaces">CAN Interfaces</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <SystemOverviewCard
              title="Server Configuration"
              icon={<Settings className="h-5 w-5" />}
              data={systemSettings?.server}
              status={systemStatus?.server_status}
            />
            <SystemOverviewCard
              title="CAN Bus Settings"
              icon={<Network className="h-5 w-5" />}
              data={systemSettings?.can}
              status={canInterfaces?.some(i => i.is_active) ? 'active' : 'inactive'}
            />
            <SystemOverviewCard
              title="Security Settings"
              icon={<Shield className="h-5 w-5" />}
              data={systemSettings?.security}
              status={systemSettings?.security?.api_key_required ? 'secured' : 'open'}
            />
            <SystemOverviewCard
              title="Data Persistence"
              icon={<Database className="h-5 w-5" />}
              data={systemSettings?.persistence}
              status={systemSettings?.persistence?.enabled ? 'enabled' : 'disabled'}
            />
            <SystemOverviewCard
              title="Advanced Diagnostics"
              icon={<Monitor className="h-5 w-5" />}
              data={systemSettings?.advanced_diagnostics}
              status={systemSettings?.advanced_diagnostics?.enabled ? 'enabled' : 'disabled'}
            />
            <SystemOverviewCard
              title="Performance Analytics"
              icon={<Zap className="h-5 w-5" />}
              data={systemSettings?.performance_analytics}
              status={systemSettings?.performance_analytics?.enabled ? 'enabled' : 'disabled'}
            />
          </div>
        </TabsContent>

        {/* Features Tab */}
        <TabsContent value="features">
          <FeatureManagementPanel
            featureManagement={featureManagement}
            isLoading={featuresLoading}
            onFeatureToggle={handleFeatureToggle}
            isUpdating={updateFeatureMutation.isPending}
          />
        </TabsContent>

        {/* Protocols Tab */}
        <TabsContent value="protocols">
          <ProtocolConfigurationPanel
            systemSettings={systemSettings}
            onValidation={handleValidation}
          />
        </TabsContent>

        {/* CAN Interfaces Tab */}
        <TabsContent value="interfaces">
          <CANInterfacePanel
            interfaces={canInterfaces}
            isLoading={interfacesLoading}
          />
        </TabsContent>

        {/* System Tab */}
        <TabsContent value="system">
          <SystemConfigurationPanel
            systemSettings={systemSettings}
            coachConfig={coachConfig}
            isLoading={coachLoading}
          />
        </TabsContent>

        {/* Advanced Tab */}
        <TabsContent value="advanced">
          <AdvancedConfigurationPanel
            systemSettings={systemSettings}
            validationResults={validationResults}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// System Overview Card Component
interface SystemOverviewCardProps {
  title: string;
  icon: React.ReactNode;
  data: unknown;
  status: string;
}

function SystemOverviewCard({ title, icon, data, status }: SystemOverviewCardProps) {
  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'running':
      case 'active':
      case 'enabled':
      case 'secured':
        return 'default';
      case 'warning':
      case 'inactive':
        return 'secondary';
      case 'error':
      case 'disabled':
      case 'open':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm font-medium">
          <div className="flex items-center">
            {icon}
            <span className="ml-2">{title}</span>
          </div>
          <Badge variant={getStatusVariant(status)} className="text-xs">
            {status}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1 text-sm text-muted-foreground">
          {data && Object.entries(data).slice(0, 3).map(([key, value]) => (
            <div key={key} className="flex justify-between">
              <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
              <span className="font-mono text-xs">
                {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Feature Management Panel Component
interface FeatureManagementPanelProps {
  featureManagement?: FeatureManagementResponse;
  isLoading: boolean;
  onFeatureToggle: (featureName: string, enabled: boolean) => void;
  isUpdating: boolean;
}

function FeatureManagementPanel({
  featureManagement,
  isLoading,
  onFeatureToggle,
  isUpdating
}: FeatureManagementPanelProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2">Loading features...</span>
      </div>
    );
  }

  if (!featureManagement?.features) {
    return (
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>No Feature Data</AlertTitle>
        <AlertDescription>Feature management data is not available.</AlertDescription>
      </Alert>
    );
  }

  const features = Object.entries(featureManagement.features);
  const categorizedFeatures = features.reduce((acc, [name, feature]) => {
    const category = feature.category || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push([name, feature]);
    return acc;
  }, {} as Record<string, [string, FeatureFlag][]>);

  return (
    <div className="space-y-6">
      {featureManagement.validation_errors.length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Feature Validation Errors</AlertTitle>
          <AlertDescription>
            <ul className="list-disc list-inside space-y-1">
              {featureManagement.validation_errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {Object.entries(categorizedFeatures).map(([category, categoryFeatures]) => (
        <Card key={category}>
          <CardHeader>
            <CardTitle className="capitalize">{category} Features</CardTitle>
            <CardDescription>
              {category === 'core' && 'Essential system features required for basic operation'}
              {category === 'protocol' && 'Multi-protocol support and communication features'}
              {category === 'advanced' && 'Advanced diagnostics and analytics capabilities'}
              {category === 'experimental' && 'Experimental features in development'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {categoryFeatures.map(([name, feature]) => (
                <div key={name} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium">{name}</span>
                      <Badge variant={feature.stability === 'stable' ? 'default' : 'secondary'}>
                        {feature.stability}
                      </Badge>
                      {feature.dependencies.length > 0 && (
                        <Badge variant="outline" className="text-xs">
                          {feature.dependencies.length} deps
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">{feature.description}</p>
                    {feature.dependencies.length > 0 && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Depends on: {feature.dependencies.join(', ')}
                      </p>
                    )}
                  </div>
                  <Switch
                    checked={feature.enabled}
                    onCheckedChange={(enabled) => onFeatureToggle(name, enabled)}
                    disabled={isUpdating}
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Protocol Configuration Panel Component
interface ProtocolConfigurationPanelProps {
  systemSettings?: SystemSettings;
  onValidation: (section?: string) => void;
}

function ProtocolConfigurationPanel({
  systemSettings,
  onValidation
}: ProtocolConfigurationPanelProps) {
  const protocols = [
    { name: 'RV-C', key: 'rvc', config: systemSettings?.rvc, icon: <Network className="h-5 w-5" /> },
    { name: 'J1939', key: 'j1939', config: systemSettings?.j1939, icon: <Network className="h-5 w-5" /> },
    { name: 'Firefly', key: 'firefly', config: systemSettings?.firefly, icon: <Zap className="h-5 w-5" /> },
    { name: 'Spartan K2', key: 'spartan_k2', config: systemSettings?.spartan_k2, icon: <Shield className="h-5 w-5" /> },
  ];

  const getProtocolStatus = (protocol: unknown, key: string) => {
    if (!protocol) return 'disabled';
    if (key === 'rvc') return 'enabled'; // RV-C is always enabled as the core protocol
    return (protocol as { enabled?: boolean })?.enabled ? 'enabled' : 'disabled';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {protocols.map((protocol) => {
        const status = getProtocolStatus(protocol.config, protocol.key);
        return (
          <Card key={protocol.key}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center">
                  {protocol.icon}
                  <span className="ml-2">{protocol.name} Protocol</span>
                </div>
                <Badge
                  variant={status === 'enabled' ? 'default' : 'secondary'}
                >
                  {status === 'enabled' ? 'Enabled' : 'Disabled'}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {protocol.config ? (
                <div className="space-y-3">
                  {Object.entries(protocol.config).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="capitalize text-muted-foreground">
                        {key.replace(/_/g, ' ')}:
                      </span>
                      <span className="font-mono text-xs">
                        {typeof value === 'boolean' ? (value ? 'Yes' : 'No') :
                         typeof value === 'object' ? 'Complex' : String(value)}
                      </span>
                    </div>
                  ))}
                  <Separator />
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => onValidation(protocol.key)}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    Validate {protocol.name}
                  </Button>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Configuration not available</p>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

// CAN Interface Panel Component
interface CANInterfacePanelProps {
  interfaces?: CANInterfaceMapping[];
  isLoading: boolean;
}

function CANInterfacePanel({ interfaces, isLoading }: CANInterfacePanelProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2">Loading CAN interfaces...</span>
      </div>
    );
  }

  if (!interfaces || interfaces.length === 0) {
    return (
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>No CAN Interfaces</AlertTitle>
        <AlertDescription>No CAN interface mappings are configured.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {interfaces.map((interface_mapping) => (
        <Card key={interface_mapping.logical_name}>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{interface_mapping.logical_name}</span>
              <div className="flex items-center space-x-2">
                {getStatusIcon(interface_mapping.validation_status)}
                <Badge
                  variant={interface_mapping.is_active ? 'default' : 'secondary'}
                >
                  {interface_mapping.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Physical Interface:</span>
                <p className="font-mono">{interface_mapping.physical_interface}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Bitrate:</span>
                <p className="font-mono">{interface_mapping.bitrate}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Messages:</span>
                <p className="font-mono">{interface_mapping.message_count}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Errors:</span>
                <p className="font-mono">{interface_mapping.error_count}</p>
              </div>
            </div>
            {interface_mapping.validation_message && (
              <Alert className="mt-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{interface_mapping.validation_message}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// System Configuration Panel Component
interface SystemConfigurationPanelProps {
  systemSettings?: SystemSettings;
  coachConfig?: CoachConfiguration;
  isLoading: boolean;
}

function SystemConfigurationPanel({
  systemSettings,
  coachConfig,
  isLoading
}: SystemConfigurationPanelProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2">Loading system configuration...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Coach Configuration */}
      {coachConfig && (
        <Card>
          <CardHeader>
            <CardTitle>Coach Configuration</CardTitle>
            <CardDescription>Current RV/coach model and device mappings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Model:</span>
                <p className="font-semibold">{coachConfig.model}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Year:</span>
                <p className="font-semibold">{coachConfig.year}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Manufacturer:</span>
                <p className="font-semibold">{coachConfig.manufacturer}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Config File:</span>
                <p className="font-mono text-xs">{coachConfig.config_file}</p>
              </div>
            </div>
            <div className="mt-4">
              <Badge
                variant={coachConfig.validation_status === 'valid' ? 'default' : 'destructive'}
              >
                {coachConfig.validation_status}
              </Badge>
              <span className="ml-2 text-sm text-muted-foreground">
                Last validated: {new Date(coachConfig.last_validated).toLocaleString()}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Server Configuration */}
      {systemSettings?.server && (
        <Card>
          <CardHeader>
            <CardTitle>Server Settings</CardTitle>
            <CardDescription>Core server configuration and networking</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              {Object.entries(systemSettings.server).map(([key, value]) => (
                <div key={key}>
                  <span className="text-muted-foreground capitalize">
                    {key.replace(/_/g, ' ')}:
                  </span>
                  <p className="font-mono text-xs">
                    {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Logging Configuration */}
      {systemSettings?.logging && (
        <Card>
          <CardHeader>
            <CardTitle>Logging Configuration</CardTitle>
            <CardDescription>System logging levels and output settings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              {Object.entries(systemSettings.logging).map(([key, value]) => (
                <div key={key}>
                  <span className="text-muted-foreground capitalize">
                    {key.replace(/_/g, ' ')}:
                  </span>
                  <p className="font-mono text-xs">
                    {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Advanced Configuration Panel Component
interface AdvancedConfigurationPanelProps {
  systemSettings?: SystemSettings;
  validationResults: Record<string, unknown>;
}

function AdvancedConfigurationPanel({
  systemSettings,
  validationResults
}: AdvancedConfigurationPanelProps) {
  return (
    <div className="space-y-6">
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Advanced Configuration</AlertTitle>
        <AlertDescription>
          These settings are for advanced users only. Incorrect configuration may cause system instability.
        </AlertDescription>
      </Alert>

      {/* Environment Variables */}
      {systemSettings?.environment_variables && (
        <Card>
          <CardHeader>
            <CardTitle>Environment Variables</CardTitle>
            <CardDescription>
              Current environment variable settings (showing COACHIQ_* variables only)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {Object.entries(systemSettings.environment_variables)
                .filter(([key]) => key.startsWith('COACHIQ_'))
                .map(([key, value]) => (
                  <div key={key} className="flex justify-between p-2 bg-muted rounded text-sm">
                    <span className="font-mono text-xs">{key}</span>
                    <span className="font-mono text-xs truncate ml-4" title={value}>
                      {value}
                    </span>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuration Sources */}
      {systemSettings?.config_sources && (
        <Card>
          <CardHeader>
            <CardTitle>Configuration Sources</CardTitle>
            <CardDescription>
              Sources and precedence for configuration values
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(systemSettings.config_sources).map(([key, source]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="font-medium">{key}</span>
                  <span className="text-muted-foreground">{source}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Validation Results */}
      {Object.keys(validationResults).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Validation Results</CardTitle>
            <CardDescription>
              Recent configuration validation results
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(validationResults).map(([section, result]) => (
                <div key={section}>
                  <h4 className="font-semibold capitalize mb-2">{section}</h4>
                  <div className="space-y-2">
                    {result.errors?.length > 0 && (
                      <Alert variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>Errors</AlertTitle>
                        <AlertDescription>
                          <ul className="list-disc list-inside">
                            {result.errors.map((error: string, index: number) => (
                              <li key={index}>{error}</li>
                            ))}
                          </ul>
                        </AlertDescription>
                      </Alert>
                    )}
                    {result.warnings?.length > 0 && (
                      <Alert>
                        <AlertTriangle className="h-4 w-4" />
                        <AlertTitle>Warnings</AlertTitle>
                        <AlertDescription>
                          <ul className="list-disc list-inside">
                            {result.warnings.map((warning: string, index: number) => (
                              <li key={index}>{warning}</li>
                            ))}
                          </ul>
                        </AlertDescription>
                      </Alert>
                    )}
                    {result.suggestions?.length > 0 && (
                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertTitle>Suggestions</AlertTitle>
                        <AlertDescription>
                          <ul className="list-disc list-inside">
                            {result.suggestions.map((suggestion: string, index: number) => (
                              <li key={index}>{suggestion}</li>
                            ))}
                          </ul>
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Helper function to get status icon
function getStatusIcon(status: string) {
  switch (status) {
    case 'running':
    case 'active':
    case 'enabled':
    case 'valid':
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    case 'warning':
    case 'inactive':
      return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    case 'error':
    case 'invalid':
    case 'disabled':
      return <AlertTriangle className="h-4 w-4 text-red-600" />;
    default:
      return <Info className="h-4 w-4 text-gray-600" />;
  }
}
