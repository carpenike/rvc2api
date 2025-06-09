/**
 * Configuration Management Page
 *
 * Provides comprehensive configuration management interface for CoachIQ system
 * with multi-protocol support, feature flag management, and real-time validation.
 */

import {
  disableFeature,
  enableFeature,
  fetchCANInterfaceMappings,
  fetchCoachConfiguration,
  fetchFeatureManagement,
  fetchSystemSettings
} from '@/api/endpoints';
import type {
  CANInterfaceMapping,
  FeatureFlag
} from '@/api/types';
import { AppLayout } from '@/components/app-layout';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  Database,
  Network,
  RefreshCw,
  Settings,
  Shield,
  Zap
} from 'lucide-react';
import { useState } from 'react';

export default function ConfigurationPage() {
  const [activeTab, setActiveTab] = useState('overview');
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

  // Mutations
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

  if (settingsLoading) {
    return (
      <AppLayout pageTitle="Configuration Management">
        <div className="container mx-auto p-6">
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-2 text-lg">Loading configuration...</span>
          </div>
        </div>
      </AppLayout>
    );
  }

  if (settingsError) {
    return (
      <AppLayout pageTitle="Configuration Management">
        <div className="container mx-auto p-6">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Configuration Error</AlertTitle>
            <AlertDescription>
              Failed to load system configuration. Please check your connection and try again.
            </AlertDescription>
          </Alert>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout pageTitle="Configuration Management">
      <div className="container mx-auto p-6 space-y-6">
        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => queryClient.invalidateQueries()}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Configuration Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="features">Features</TabsTrigger>
            <TabsTrigger value="interfaces">CAN Interfaces</TabsTrigger>
            <TabsTrigger value="protocols">Protocols</TabsTrigger>
            <TabsTrigger value="coach">Coach Config</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Settings className="h-5 w-5 mr-2" />
                  System Settings Overview
                </CardTitle>
                <CardDescription>
                  Current system configuration and operational parameters
                </CardDescription>
              </CardHeader>
              <CardContent>
                {systemSettings ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <h4 className="font-semibold text-sm">Environment</h4>
                      <div className="text-sm space-y-1">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Variables:</span>
                          <span>{Object.keys(systemSettings.environment_variables || {}).length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Sources:</span>
                          <span>{Object.keys(systemSettings.config_sources || {}).length}</span>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <h4 className="font-semibold text-sm">Server</h4>
                      <div className="text-sm space-y-1">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Host:</span>
                          <span>{systemSettings.server?.host || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Port:</span>
                          <span>{systemSettings.server?.port || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <h4 className="font-semibold text-sm">Persistence</h4>
                      <div className="text-sm space-y-1">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Enabled:</span>
                          <span>{systemSettings.persistence?.enabled ? 'Yes' : 'No'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Backend:</span>
                          <span>{systemSettings.persistence?.backend_type || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No system settings available
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Features Tab */}
          <TabsContent value="features" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Zap className="h-5 w-5 mr-2" />
                  Feature Management
                </CardTitle>
                <CardDescription>
                  Enable or disable system features and capabilities
                </CardDescription>
              </CardHeader>
              <CardContent>
                {featureManagement && Object.keys(featureManagement.features).length > 0 ? (
                  <div className="space-y-4">
                    {Object.entries(featureManagement.features).map(([featureName, feature]: [string, FeatureFlag]) => (
                      <div key={featureName} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <h4 className="font-medium">{feature.name}</h4>
                            <Badge variant={feature.enabled ? 'default' : 'secondary'}>
                              {feature.enabled ? 'Enabled' : 'Disabled'}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {feature.description || 'No description available'}
                          </p>
                          {feature.dependencies && feature.dependencies.length > 0 && (
                            <p className="text-xs text-muted-foreground">
                              Dependencies: {feature.dependencies.join(', ')}
                            </p>
                          )}
                        </div>
                        <Switch
                          checked={feature.enabled}
                          onCheckedChange={(enabled) => handleFeatureToggle(featureName, enabled)}
                          disabled={updateFeatureMutation.isPending}
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    {featuresLoading ? 'Loading features...' : 'No features available'}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* CAN Interfaces Tab */}
          <TabsContent value="interfaces" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Network className="h-5 w-5 mr-2" />
                  CAN Interface Mappings
                </CardTitle>
                <CardDescription>
                  Current CAN bus interface configurations and status
                </CardDescription>
              </CardHeader>
              <CardContent>
                {canInterfaces && canInterfaces.length > 0 ? (
                  <div className="space-y-4">
                    {canInterfaces.map((iface: CANInterfaceMapping) => (
                      <div key={iface.logical_name} className="p-4 border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium">{iface.logical_name}</h4>
                          <Badge variant={iface.is_active ? 'default' : 'secondary'}>
                            {iface.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">Physical:</span>
                            <span className="ml-2">{iface.physical_interface}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Bitrate:</span>
                            <span className="ml-2">{iface.bitrate}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Messages:</span>
                            <span className="ml-2">{iface.message_count}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Status:</span>
                            <span className="ml-2">{iface.validation_status}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    {interfacesLoading ? 'Loading interfaces...' : 'No CAN interfaces configured'}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Protocols Tab */}
          <TabsContent value="protocols" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Shield className="h-5 w-5 mr-2" />
                  Protocol Configuration
                </CardTitle>
                <CardDescription>
                  Multi-protocol support and configuration status
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-muted-foreground">
                  Protocol configuration coming soon
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Coach Configuration Tab */}
          <TabsContent value="coach" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Database className="h-5 w-5 mr-2" />
                  Coach Configuration
                </CardTitle>
                <CardDescription>
                  Vehicle-specific configuration and device mappings
                </CardDescription>
              </CardHeader>
              <CardContent>
                {coachConfig ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <h4 className="font-semibold">Vehicle Information</h4>
                        <div className="text-sm space-y-1">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Manufacturer:</span>
                            <span>{coachConfig.manufacturer || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Model:</span>
                            <span>{coachConfig.model || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Year:</span>
                            <span>{coachConfig.year || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Config File:</span>
                            <span>{coachConfig.config_file || 'N/A'}</span>
                          </div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <h4 className="font-semibold">System Configuration</h4>
                        <div className="text-sm space-y-1">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Device Mappings:</span>
                            <span>{Object.keys(coachConfig.device_mappings || {}).length}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Interface Requirements:</span>
                            <span>{coachConfig.interface_requirements?.length || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Validation Status:</span>
                            <Badge variant={coachConfig.validation_status === 'valid' ? 'default' : 'destructive'}>
                              {coachConfig.validation_status || 'Unknown'}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    {coachLoading ? 'Loading coach configuration...' : 'No coach configuration available'}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

        </Tabs>
      </div>
    </AppLayout>
  );
}
