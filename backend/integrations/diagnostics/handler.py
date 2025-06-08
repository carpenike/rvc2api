"""
Advanced Diagnostic Handler

Main handler for comprehensive diagnostic processing across all protocols.
Provides fault correlation, DTC analysis, and integration with existing
RV-C, J1939, and OEM-specific diagnostic capabilities.
"""

import asyncio
import logging
import time
from collections import deque
from typing import Any

from backend.core.config import Settings
from backend.integrations.diagnostics.config import AdvancedDiagnosticsSettings
from backend.integrations.diagnostics.models import (
    DiagnosticTroubleCode,
    DTCSeverity,
    FaultCorrelation,
    ProtocolType,
    SystemHealthStatus,
    SystemType,
)

logger = logging.getLogger(__name__)


class DiagnosticHandler:
    """
    Advanced diagnostic handler for multi-protocol RV systems.

    Provides comprehensive diagnostic capabilities including:
    - Cross-protocol DTC processing
    - Fault correlation analysis
    - System health monitoring
    - Integration with existing protocol handlers
    """

    def __init__(self, settings: Settings):
        """Initialize the diagnostic handler."""
        self.settings = settings
        self.diag_settings = getattr(
            settings, "advanced_diagnostics", AdvancedDiagnosticsSettings()
        )

        # DTC storage and tracking
        self._active_dtcs: dict[tuple[int, ProtocolType, int], DiagnosticTroubleCode] = {}
        self._historical_dtcs: list[DiagnosticTroubleCode] = []
        self._dtc_history: deque = deque(maxlen=10000)  # Recent DTC events

        # System health tracking
        self._system_health: dict[SystemType, SystemHealthStatus] = {}
        self._initialize_system_health()

        # Correlation analysis
        self._correlation_buffer: deque = deque(maxlen=1000)  # Recent events for correlation
        self._correlation_cache: dict[str, FaultCorrelation] = {}

        # Performance tracking
        self._processing_stats = {
            "dtcs_processed": 0,
            "correlations_found": 0,
            "predictions_made": 0,
            "processing_time_ms": 0.0,
        }

        # Background tasks
        self._background_tasks: list[asyncio.Task] = []
        self._running = False

        logger.info(
            f"Advanced diagnostics handler initialized (enabled: {self.diag_settings.enabled})"
        )

    def _initialize_system_health(self) -> None:
        """Initialize system health tracking for all system types."""
        for system_type in SystemType:
            if system_type != SystemType.UNKNOWN:
                self._system_health[system_type] = SystemHealthStatus(
                    system_type=system_type, health_score=1.0
                )

    async def startup(self) -> None:
        """Start background diagnostic processing tasks."""
        if not self.diag_settings.enabled:
            logger.info("Advanced diagnostics disabled, skipping startup")
            return

        self._running = True

        # Start background correlation analysis
        correlation_task = asyncio.create_task(self._correlation_analysis_loop())
        self._background_tasks.append(correlation_task)

        # Start health assessment
        health_task = asyncio.create_task(self._health_assessment_loop())
        self._background_tasks.append(health_task)

        logger.info("Advanced diagnostics background tasks started")

    async def shutdown(self) -> None:
        """Shutdown background tasks."""
        self._running = False

        # Cancel all background tasks
        for task in self._background_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        self._background_tasks.clear()
        logger.info("Advanced diagnostics shutdown complete")

    def process_dtc(
        self,
        code: int,
        protocol: ProtocolType,
        system_type: SystemType,
        source_address: int = 0,
        pgn: int | None = None,
        dgn: int | None = None,
        raw_data: bytes | None = None,
        severity: DTCSeverity | None = None,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> DiagnosticTroubleCode:
        """
        Process a diagnostic trouble code from any protocol.

        Args:
            code: DTC code number
            protocol: Source protocol (RV-C, J1939, etc.)
            system_type: Affected system type
            source_address: CAN source address
            pgn: J1939 PGN (if applicable)
            dgn: RV-C DGN (if applicable)
            raw_data: Raw message data
            severity: Override severity classification
            description: Human-readable description
            metadata: Additional metadata

        Returns:
            Processed DiagnosticTroubleCode
        """
        start_time = time.perf_counter()

        try:
            # Create DTC key for tracking
            dtc_key = (code, protocol, source_address)

            # Check if this is an existing DTC
            if dtc_key in self._active_dtcs:
                existing_dtc = self._active_dtcs[dtc_key]
                existing_dtc.update_occurrence()
                dtc = existing_dtc
                logger.debug(
                    f"Updated existing DTC {code} from {protocol.value} (count: {dtc.occurrence_count})"
                )
            else:
                # Create new DTC
                dtc = DiagnosticTroubleCode(
                    code=code,
                    protocol=protocol,
                    system_type=system_type,
                    severity=severity or self._classify_severity(code, system_type, protocol),
                    source_address=source_address,
                    pgn=pgn,
                    dgn=dgn,
                    raw_data=raw_data,
                    description=description or self._get_dtc_description(code, protocol),
                    metadata=metadata or {},
                )

                # Add default recommendations
                dtc.possible_causes = self._get_possible_causes(code, protocol, system_type)
                dtc.recommended_actions = self._get_recommended_actions(code, protocol, system_type)

                # Store active DTC
                self._active_dtcs[dtc_key] = dtc
                logger.info(
                    f"New DTC {code} from {protocol.value} system {system_type.value} (severity: {dtc.severity.value})"
                )

            # Add to correlation buffer for analysis
            self._correlation_buffer.append(dtc)

            # Add to history
            self._dtc_history.append((time.time(), dtc))

            # Update system health
            self._update_system_health(dtc)

            # Update processing stats
            self._processing_stats["dtcs_processed"] += 1
            processing_time = (time.perf_counter() - start_time) * 1000
            self._processing_stats["processing_time_ms"] += processing_time

            return dtc

        except Exception as e:
            logger.error(f"Error processing DTC {code} from {protocol.value}: {e}")
            # Return a basic DTC even if processing fails
            return DiagnosticTroubleCode(
                code=code,
                protocol=protocol,
                system_type=system_type,
                severity=DTCSeverity.MEDIUM,
                description=f"Error processing DTC: {e}",
            )

    def resolve_dtc(self, code: int, protocol: ProtocolType, source_address: int = 0) -> bool:
        """
        Mark a DTC as resolved.

        Args:
            code: DTC code number
            protocol: Source protocol
            source_address: CAN source address

        Returns:
            True if DTC was found and resolved
        """
        dtc_key = (code, protocol, source_address)

        if dtc_key in self._active_dtcs:
            dtc = self._active_dtcs[dtc_key]
            dtc.resolve()

            # Move to historical storage
            self._historical_dtcs.append(dtc)
            del self._active_dtcs[dtc_key]

            logger.info(f"Resolved DTC {code} from {protocol.value}")
            return True

        return False

    def get_active_dtcs(
        self,
        system_type: SystemType | None = None,
        severity: DTCSeverity | None = None,
        protocol: ProtocolType | None = None,
    ) -> list[DiagnosticTroubleCode]:
        """
        Get active DTCs with optional filtering.

        Args:
            system_type: Filter by system type
            severity: Filter by severity level
            protocol: Filter by protocol

        Returns:
            List of matching active DTCs
        """
        dtcs = list(self._active_dtcs.values())

        if system_type:
            dtcs = [dtc for dtc in dtcs if dtc.system_type == system_type]

        if severity:
            dtcs = [dtc for dtc in dtcs if dtc.severity == severity]

        if protocol:
            dtcs = [dtc for dtc in dtcs if dtc.protocol == protocol]

        # Sort by severity and occurrence time
        severity_order = {
            DTCSeverity.CRITICAL: 0,
            DTCSeverity.HIGH: 1,
            DTCSeverity.MEDIUM: 2,
            DTCSeverity.LOW: 3,
            DTCSeverity.INFORMATIONAL: 4,
        }

        return sorted(dtcs, key=lambda d: (severity_order[d.severity], d.first_occurrence))

    def get_system_health(self, system_type: SystemType | None = None) -> dict[str, Any]:
        """
        Get system health status.

        Args:
            system_type: Specific system to query, or None for all systems

        Returns:
            System health information
        """
        if system_type:
            health = self._system_health.get(system_type)
            return health.to_dict() if health else {}

        return {system.value: health.to_dict() for system, health in self._system_health.items()}

    def get_fault_correlations(
        self, time_window_seconds: float | None = None
    ) -> list[FaultCorrelation]:
        """
        Get fault correlations within the specified time window.

        Args:
            time_window_seconds: Time window for correlation analysis

        Returns:
            List of fault correlations found
        """
        return list(self._correlation_cache.values())

    def get_diagnostic_statistics(self) -> dict[str, Any]:
        """Get diagnostic processing statistics."""
        return {
            "active_dtcs": len(self._active_dtcs),
            "historical_dtcs": len(self._historical_dtcs),
            "correlations_cached": len(self._correlation_cache),
            "system_health_scores": {
                system.value: health.health_score for system, health in self._system_health.items()
            },
            "processing_stats": self._processing_stats.copy(),
        }

    # Internal helper methods

    def _classify_severity(
        self, code: int, system_type: SystemType, protocol: ProtocolType
    ) -> DTCSeverity:
        """Classify DTC severity based on code, system, and protocol."""
        # Critical codes from configuration
        if code in self.diag_settings.critical_dtc_codes:
            return DTCSeverity.CRITICAL

        # High priority systems
        if system_type.value in self.diag_settings.high_priority_systems:
            if code < 1000:  # Lower codes often indicate more serious issues
                return DTCSeverity.HIGH
            return DTCSeverity.MEDIUM

        # Protocol-specific severity rules
        if protocol == ProtocolType.J1939 and system_type in [
            SystemType.ENGINE,
            SystemType.BRAKES,
            SystemType.STEERING,
        ]:
            # J1939 severity classification
            return DTCSeverity.HIGH if code < 2000 else DTCSeverity.MEDIUM

        # Default classification
        return DTCSeverity.MEDIUM

    def _get_dtc_description(self, code: int, protocol: ProtocolType) -> str:
        """Get human-readable description for DTC."""
        # This would typically look up descriptions from a database
        # For now, provide generic descriptions
        protocol_map = {
            ProtocolType.RVC: "RV-C",
            ProtocolType.J1939: "J1939",
            ProtocolType.FIREFLY: "Firefly",
            ProtocolType.SPARTAN_K2: "Spartan K2",
        }

        return f"{protocol_map.get(protocol, 'Unknown')} diagnostic code {code}"

    def _get_possible_causes(
        self, code: int, protocol: ProtocolType, system_type: SystemType
    ) -> list[str]:
        """Get possible causes for a DTC."""
        # This would typically be looked up from a knowledge base
        # For now, provide generic causes based on system type
        causes = []

        if system_type == SystemType.ENGINE:
            causes = [
                "Sensor malfunction",
                "Wiring issue",
                "Component failure",
                "Fuel system problem",
            ]
        elif system_type == SystemType.ELECTRICAL:
            causes = [
                "Voltage irregularity",
                "Connection problem",
                "Component overload",
                "Ground fault",
            ]
        elif system_type == SystemType.BRAKES:
            causes = [
                "Air pressure low",
                "Sensor fault",
                "Valve malfunction",
                "Brake component wear",
            ]
        else:
            causes = ["Component malfunction", "Wiring issue", "Configuration problem"]

        return causes

    def _get_recommended_actions(
        self, code: int, protocol: ProtocolType, system_type: SystemType
    ) -> list[str]:
        """Get recommended actions for a DTC."""
        # This would typically be looked up from a service manual database
        actions = []

        if system_type == SystemType.ENGINE:
            actions = [
                "Check engine sensors",
                "Inspect wiring harness",
                "Review fuel system",
                "Consult service manual",
            ]
        elif system_type == SystemType.ELECTRICAL:
            actions = [
                "Check voltage levels",
                "Inspect connections",
                "Test components",
                "Verify ground connections",
            ]
        elif system_type == SystemType.BRAKES:
            actions = [
                "Check air pressure",
                "Inspect brake components",
                "Test sensors",
                "Verify system operation",
            ]
        else:
            actions = [
                "Inspect system components",
                "Check connections",
                "Consult technical documentation",
            ]

        return actions

    def _update_system_health(self, dtc: DiagnosticTroubleCode) -> None:
        """Update system health based on new DTC."""
        system_health = self._system_health.get(dtc.system_type)
        if not system_health:
            return

        # Add DTC to system health
        if dtc not in system_health.active_dtcs:
            system_health.active_dtcs.append(dtc)

        # Recalculate health score
        health_score = self._calculate_health_score(dtc.system_type)
        system_health.update_health_score(health_score)

    def _calculate_health_score(self, system_type: SystemType) -> float:
        """Calculate health score for a system based on active DTCs."""
        system_health = self._system_health.get(system_type)
        if not system_health:
            return 1.0

        if not system_health.active_dtcs:
            return 1.0

        # Calculate score based on DTC severity and count
        score = 1.0
        severity_weights = {
            DTCSeverity.CRITICAL: 0.5,
            DTCSeverity.HIGH: 0.3,
            DTCSeverity.MEDIUM: 0.15,
            DTCSeverity.LOW: 0.05,
            DTCSeverity.INFORMATIONAL: 0.01,
        }

        for dtc in system_health.active_dtcs:
            weight = severity_weights.get(dtc.severity, 0.1)
            score -= weight

        return max(0.0, score)

    async def _correlation_analysis_loop(self) -> None:
        """Background task for fault correlation analysis."""
        while self._running:
            try:
                if self.diag_settings.enable_fault_correlation:
                    await self._analyze_correlations()

                await asyncio.sleep(self.diag_settings.correlation_time_window_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in correlation analysis: {e}")
                await asyncio.sleep(5.0)

    async def _health_assessment_loop(self) -> None:
        """Background task for system health assessment."""
        while self._running:
            try:
                await self._assess_system_health()
                await asyncio.sleep(self.diag_settings.health_assessment_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health assessment: {e}")
                await asyncio.sleep(5.0)

    async def _analyze_correlations(self) -> None:
        """Analyze fault correlations in the correlation buffer."""
        if len(self._correlation_buffer) < 2:
            return

        # Analyze DTCs within time window
        current_time = time.time()
        time_window = self.diag_settings.correlation_time_window_seconds

        recent_dtcs = [
            dtc
            for dtc in self._correlation_buffer
            if current_time - dtc.last_occurrence <= time_window
        ]

        if len(recent_dtcs) < 2:
            return

        # Look for correlations
        for i, primary_dtc in enumerate(recent_dtcs[:-1]):
            related_dtcs = []

            for secondary_dtc in recent_dtcs[i + 1 :]:
                # Check for correlation criteria
                if self._dtcs_correlated(primary_dtc, secondary_dtc):
                    related_dtcs.append(secondary_dtc)

            if related_dtcs:
                correlation = FaultCorrelation(
                    primary_dtc=primary_dtc,
                    related_dtcs=related_dtcs,
                    correlation_confidence=self._calculate_correlation_confidence(
                        primary_dtc, related_dtcs
                    ),
                    correlation_type=self._determine_correlation_type(primary_dtc, related_dtcs),
                    time_window_seconds=time_window,
                )

                correlation_key = (
                    f"{primary_dtc.code}_{primary_dtc.protocol.value}_{len(related_dtcs)}"
                )
                self._correlation_cache[correlation_key] = correlation

                logger.info(
                    f"Found fault correlation: primary DTC {primary_dtc.code}, {len(related_dtcs)} related DTCs"
                )
                self._processing_stats["correlations_found"] += 1

    def _dtcs_correlated(self, dtc1: DiagnosticTroubleCode, dtc2: DiagnosticTroubleCode) -> bool:
        """Determine if two DTCs are correlated."""
        # Same system type
        if dtc1.system_type == dtc2.system_type:
            return True

        # Related systems (e.g., engine and transmission)
        related_systems = {
            (SystemType.ENGINE, SystemType.TRANSMISSION),
            (SystemType.BRAKES, SystemType.SAFETY),
            (SystemType.ELECTRICAL, SystemType.POWER),
            (SystemType.SUSPENSION, SystemType.LEVELING),
        }

        system_pair = (dtc1.system_type, dtc2.system_type)
        return bool(
            system_pair in related_systems or (system_pair[1], system_pair[0]) in related_systems
        )

    def _calculate_correlation_confidence(
        self, primary_dtc: DiagnosticTroubleCode, related_dtcs: list[DiagnosticTroubleCode]
    ) -> float:
        """Calculate confidence level for fault correlation."""
        # Base confidence on timing, system relationships, and historical patterns
        confidence = 0.5  # Base confidence

        # Same source address increases confidence
        same_source = sum(
            1 for dtc in related_dtcs if dtc.source_address == primary_dtc.source_address
        )
        confidence += (same_source / len(related_dtcs)) * 0.2

        # Related systems increase confidence
        related_count = sum(1 for dtc in related_dtcs if self._dtcs_correlated(primary_dtc, dtc))
        confidence += (related_count / len(related_dtcs)) * 0.3

        return min(1.0, confidence)

    def _determine_correlation_type(
        self, primary_dtc: DiagnosticTroubleCode, related_dtcs: list[DiagnosticTroubleCode]
    ) -> str:
        """Determine the type of correlation between DTCs."""
        # Simple heuristics for correlation type
        if any(dtc.system_type == primary_dtc.system_type for dtc in related_dtcs):
            return "symptomatic"

        if primary_dtc.severity == DTCSeverity.CRITICAL:
            return "causal"

        return "temporal"

    async def _assess_system_health(self) -> None:
        """Assess overall system health and update scores."""
        for system_type, health_status in self._system_health.items():
            new_score = self._calculate_health_score(system_type)

            if abs(new_score - health_status.health_score) > 0.1:
                health_status.update_health_score(new_score)
                logger.debug(f"Updated {system_type.value} health score to {new_score:.2f}")
