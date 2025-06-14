/**
 * Health monitoring types for the CoachIQ system.
 * Compliant with IETF health+json format (draft-inadarei-api-health-check-06).
 */

export type HealthStatus = 'pass' | 'warn' | 'fail';
export type ComponentStatus = 'ok' | 'warning' | 'critical' | 'unknown';
export type SafetyClassification = 'critical' | 'safety_related' | 'position_critical' | 'operational' | 'maintenance';

export interface HealthCheck {
  status: HealthStatus;
}

export interface SystemHealthComponent {
  name: string;
  status: ComponentStatus;
  safetyclassification: SafetyClassification;
  message: string;
  lastCheck: string;
  details?: Record<string, any>;
}

export interface SystemHealth {
  status: HealthStatus;
  version: string;
  releaseId: string;
  serviceId: string;
  description: string;
  timestamp: string;
  checks: Record<string, HealthCheck>;
  issues?: {
    critical: {
      failed: string[];
      degraded: string[];
    };
    warning: {
      failed: string[];
      degraded: string[];
    };
  };
  service: {
    name: string;
    version: string;
    environment: string;
    hostname: string;
    platform: string;
  };
  response_time_ms: number;
}

export interface HealthMonitoringData {
  endpoints: Record<string, {
    total_requests: number;
    success_rate: number;
    avg_response_time_ms: number;
    consecutive_failures: number;
    health_status: ComponentStatus;
  }>;
  overall_health: ComponentStatus;
  total_requests: number;
  global_success_rate: number;
  alerts: string[];
}

// Response types for different health endpoints
export interface LivenessResponse {
  status: HealthStatus;
  version: string;
  serviceId: string;
  description: string;
  timestamp: string;
  checks: {
    process: HealthCheck;
    event_loop: HealthCheck;
  };
  response_time_ms: number;
  service: {
    name: string;
    environment: string;
  };
}

export interface StartupResponse {
  status: HealthStatus;
  version: string;
  releaseId: string;
  serviceId: string;
  description: string;
  timestamp: string;
  checks: {
    can_interface: HealthCheck;
    can_feature: HealthCheck;
  };
  response_time_ms: number;
  service: {
    name: string;
    version: string;
    environment: string;
    hostname: string;
    platform: string;
  };
}

export interface ReadinessResponse {
  status: HealthStatus;
  version: string;
  releaseId: string;
  serviceId: string;
  description: string;
  timestamp: string;
  checks: {
    hardware_initialization: HealthCheck;
    core_services: HealthCheck;
    entity_discovery: HealthCheck;
    protocol_systems: HealthCheck;
    safety_systems: HealthCheck;
    api_systems: HealthCheck;
  };
  response_time_ms: number;
  service: {
    name: string;
    version: string;
    environment: string;
    hostname: string;
    platform: string;
  };
  issues?: {
    critical: string[];
    warning: string[];
  };
  detailed_checks?: Record<string, {
    status: HealthStatus;
    details: Record<string, any>;
  }>;
  metrics?: {
    entity_count: number;
    enabled_features: number;
    critical_systems_healthy: boolean;
    warning_systems_healthy: boolean;
  };
}

// Human-readable health endpoint response
export interface HumanHealthResponse {
  status: string;
  service_name: string;
  version: string;
  environment: string;
  uptime_seconds: number;
  uptime_human: string;
  timestamp: string;
  entity_count: number;
  can_interfaces: string[];
  protocols_enabled: string[];
  hostname: string;
  platform: string;
  python_version: string;
}

// Monitoring endpoint response
export interface HealthMonitoringResponse {
  monitoring_summary: HealthMonitoringData;
  timestamp: string;
  description: string;
}
