"""
Security Manager for RV-C CANbus networks.

This module provides security validation, anomaly detection, and rate limiting
for CAN messages to protect against malicious or faulty devices.
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Anomaly:
    """Represents a detected anomaly in CAN traffic."""

    timestamp: float
    anomaly_type: str
    source_address: int
    dgn: int | None
    severity: str  # "low", "medium", "high", "critical"
    description: str
    evidence: dict[str, Any]


@dataclass
class RateLimit:
    """Rate limiting configuration."""

    messages_per_second: float
    burst_size: int
    window_seconds: float = 1.0


class SecurityManager:
    """
    Security manager for RV-C CANbus networks.

    Provides:
    - Source address validation
    - Anomaly detection
    - Rate limiting
    - Security event logging
    """

    def __init__(self, settings: Any = None):
        """
        Initialize the security manager.

        Args:
            settings: Application settings instance (uses get_settings() if None)
        """
        self.settings = settings or get_settings()

        # Message tracking for anomaly detection
        self._message_counts: dict[int, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._dgn_counts: dict[int, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._source_stats: dict[int, dict[str, Any]] = defaultdict(self._create_source_stats)

        # Rate limiting
        self._rate_limits: dict[str, RateLimit] = {}
        self._rate_limit_violations: dict[int, float] = {}

        # Anomaly tracking
        self._anomalies: list[Anomaly] = []
        self._max_anomalies = 1000  # Ring buffer

        # Security configuration
        self._setup_security_rules()

        logger.info("Security manager initialized")

    def _create_source_stats(self) -> dict[str, Any]:
        """Create initial statistics for a source address."""
        return {
            "first_seen": time.time(),
            "last_seen": time.time(),
            "message_count": 0,
            "dgns_seen": set(),
            "suspicious_activity": 0,
            "rate_violations": 0,
        }

    def _setup_security_rules(self) -> None:
        """Setup security rules and rate limits."""
        # Default rate limits for different message types
        self._rate_limits = {
            # Critical control messages - stricter limits
            "control": RateLimit(messages_per_second=10.0, burst_size=5),
            # Status messages - more lenient
            "status": RateLimit(messages_per_second=50.0, burst_size=20),
            # Diagnostic messages - moderate limits
            "diagnostic": RateLimit(messages_per_second=5.0, burst_size=2),
            # Default for unknown message types
            "default": RateLimit(messages_per_second=20.0, burst_size=10),
        }

        # Get controller source address
        try:
            self._controller_addr = int(self.settings.controller_source_addr, 16)
        except (ValueError, AttributeError):
            self._controller_addr = 0xF9  # Default

    def validate_source_address(self, source_address: int, dgn: int) -> bool:
        """
        Validate message source against permissions and known good sources.

        Args:
            source_address: Source address from CAN message
            dgn: DGN (Data Group Number)

        Returns:
            True if source is authorized, False otherwise
        """
        # Always allow our own controller
        if source_address == self._controller_addr:
            return True

        # Define valid source address ranges for RV-C
        valid_ranges = [
            (0x00, 0x7F),  # Standard device range
            (0x80, 0xF7),  # Extended device range
            # 0xF8-0xFF are reserved for special purposes
        ]

        # Check if source is in valid range
        in_valid_range = any(
            min_addr <= source_address <= max_addr for min_addr, max_addr in valid_ranges
        )

        if not in_valid_range:
            self._record_anomaly(
                "invalid_source_range",
                source_address,
                dgn,
                "high",
                f"Source address {source_address:02X} outside valid range",
                {"source_address": source_address, "dgn": dgn},
            )
            return False

        # Check for suspicious rapid address changes (address hopping)
        current_time = time.time()
        recent_sources = set()

        # Look at recent messages from the last 10 seconds
        for src_addr, stats in self._source_stats.items():
            if current_time - stats["last_seen"] < 10.0:
                recent_sources.add(src_addr)

        # Flag if we see too many unique sources in a short time
        if len(recent_sources) > 20:  # Threshold for suspicious activity
            self._record_anomaly(
                "address_hopping",
                source_address,
                dgn,
                "medium",
                f"Too many unique source addresses ({len(recent_sources)}) in short timeframe",
                {"recent_sources": len(recent_sources), "timeframe": 10.0},
            )

        return True

    def detect_anomalous_traffic(self, messages: list[dict[str, Any]]) -> list[Anomaly]:
        """
        Analyze message patterns for anomalies.

        Args:
            messages: List of recent CAN messages

        Returns:
            List of detected anomalies
        """
        anomalies = []
        current_time = time.time()

        # Group messages by source
        by_source = defaultdict(list)
        for msg in messages:
            source = msg.get("source_address", 0)
            by_source[source].append(msg)

        for source_address, source_messages in by_source.items():
            # Update source statistics
            stats = self._source_stats[source_address]
            stats["last_seen"] = current_time
            stats["message_count"] += len(source_messages)

            # Collect DGNs for this source
            dgns_in_batch = set()
            for msg in source_messages:
                if "dgn" in msg:
                    dgns_in_batch.add(msg["dgn"])
                    stats["dgns_seen"].add(msg["dgn"])

            # 1. Detect message flooding
            recent_count = len(
                [msg for msg in source_messages if current_time - msg.get("timestamp", 0) < 1.0]
            )

            if recent_count > 100:  # More than 100 messages per second
                anomaly = self._record_anomaly(
                    "message_flooding",
                    source_address,
                    None,
                    "high",
                    f"Source {source_address:02X} sending {recent_count} messages/second",
                    {"message_rate": recent_count, "timeframe": 1.0},
                )
                anomalies.append(anomaly)

            # 2. Detect DGN scanning (sending to many different DGNs)
            if len(dgns_in_batch) > 20:  # Threshold for DGN scanning
                anomaly = self._record_anomaly(
                    "dgn_scanning",
                    source_address,
                    None,
                    "medium",
                    f"Source {source_address:02X} sending to {len(dgns_in_batch)} different DGNs",
                    {
                        "dgn_count": len(dgns_in_batch),
                        "dgns": list(dgns_in_batch)[:10],
                    },  # Limit evidence size
                )
                anomalies.append(anomaly)

            # 3. Detect malformed messages
            for msg in source_messages:
                data_length = len(msg.get("data", b""))
                expected_length = 8  # Standard CAN frame

                if data_length > expected_length:
                    anomaly = self._record_anomaly(
                        "oversized_message",
                        source_address,
                        msg.get("dgn"),
                        "medium",
                        f"Message with {data_length} bytes (expected {expected_length})",
                        {"data_length": data_length, "expected": expected_length},
                    )
                    anomalies.append(anomaly)

            # 4. Detect new sources (potential impersonation)
            if stats["message_count"] == len(source_messages):  # First time seeing this source
                # Check if this source address was recently used by another device
                for other_source, other_stats in self._source_stats.items():
                    if (
                        other_source != source_address
                        and current_time - other_stats["last_seen"] < 60.0  # Recently active
                        and len(stats["dgns_seen"] & other_stats["dgns_seen"]) > 0
                    ):  # Overlapping DGNs
                        anomaly = self._record_anomaly(
                            "potential_impersonation",
                            source_address,
                            None,
                            "high",
                            f"New source {source_address:02X} using DGNs recently used by {other_source:02X}",
                            {
                                "new_source": source_address,
                                "existing_source": other_source,
                                "overlapping_dgns": list(
                                    stats["dgns_seen"] & other_stats["dgns_seen"]
                                ),
                            },
                        )
                        anomalies.append(anomaly)
                        break

        return anomalies

    def rate_limit_commands(self, source_address: int, dgn: int | None = None) -> bool:
        """
        Check if a command should be rate limited.

        Args:
            source_address: Source address of the command
            dgn: Optional DGN for more specific rate limiting

        Returns:
            True if command should be allowed, False if rate limited
        """
        current_time = time.time()

        # Determine message type for rate limiting
        message_type = self._classify_message_type(dgn)
        rate_limit = self._rate_limits.get(message_type, self._rate_limits["default"])

        # Track messages from this source
        source_messages = self._message_counts[source_address]

        # Clean old messages outside the window
        while source_messages and current_time - source_messages[0] > rate_limit.window_seconds:
            source_messages.popleft()

        # Check if we're over the rate limit
        if (
            len(source_messages) >= rate_limit.burst_size
            and len(source_messages) >= rate_limit.messages_per_second * rate_limit.window_seconds
        ):
            # Rate limited
            self._rate_limit_violations[source_address] = current_time

            self._record_anomaly(
                "rate_limit_violation",
                source_address,
                dgn,
                "medium",
                f"Source {source_address:02X} exceeded rate limit ({rate_limit.messages_per_second}/sec)",
                {
                    "rate_limit": rate_limit.messages_per_second,
                    "actual_rate": len(source_messages) / rate_limit.window_seconds,
                    "message_type": message_type,
                },
            )

            return False

        # Allow the message and record it
        source_messages.append(current_time)
        return True

    def _classify_message_type(self, dgn: int | None) -> str:
        """
        Classify message type for rate limiting.

        Args:
            dgn: DGN (Data Group Number)

        Returns:
            Message type classification
        """
        if dgn is None:
            return "default"

        # Extract PGN from DGN
        pgn = dgn & 0x3FFFF

        # Common RV-C PGN classifications
        if pgn in range(0x1FEF0, 0x1FEF8):  # Command ranges
            return "control"
        if pgn in range(0x1FFB0, 0x1FFC0):  # Status ranges
            return "status"
        if pgn in range(0x1FEC0, 0x1FED0):  # Diagnostic ranges
            return "diagnostic"
        return "default"

    def _record_anomaly(
        self,
        anomaly_type: str,
        source_address: int,
        dgn: int | None,
        severity: str,
        description: str,
        evidence: dict[str, Any],
    ) -> Anomaly:
        """Record an anomaly for tracking and analysis."""
        anomaly = Anomaly(
            timestamp=time.time(),
            anomaly_type=anomaly_type,
            source_address=source_address,
            dgn=dgn,
            severity=severity,
            description=description,
            evidence=evidence,
        )

        # Add to ring buffer
        self._anomalies.append(anomaly)
        if len(self._anomalies) > self._max_anomalies:
            self._anomalies.pop(0)

        # Update source statistics
        if source_address in self._source_stats:
            self._source_stats[source_address]["suspicious_activity"] += 1

        # Log based on severity
        log_msg = f"Security anomaly: {anomaly_type} - {description}"

        if severity == "critical":
            logger.critical(log_msg)
        elif severity == "high":
            logger.error(log_msg)
        elif severity == "medium":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        return anomaly

    def log_security_event(self, event_type: str, details: dict[str, Any]) -> None:
        """
        Log a security-related event.

        Args:
            event_type: Type of security event
            details: Event details dictionary
        """
        logger.info(f"Security event: {event_type} - {details}")

        # Could be extended to send to external security monitoring systems
        # or integrate with SIEM tools

    def get_security_status(self) -> dict[str, Any]:
        """
        Get current security status and statistics.

        Returns:
            Dictionary with security status information
        """
        current_time = time.time()

        # Count recent anomalies by severity
        recent_anomalies = [
            a for a in self._anomalies if current_time - a.timestamp < 3600
        ]  # Last hour
        anomaly_counts = defaultdict(int)
        for anomaly in recent_anomalies:
            anomaly_counts[anomaly.severity] += 1

        # Count active sources
        active_sources = len(
            [
                stats
                for stats in self._source_stats.values()
                if current_time - stats["last_seen"] < 300  # Active in last 5 minutes
            ]
        )

        # Count recent rate limit violations
        recent_violations = len(
            [
                timestamp
                for timestamp in self._rate_limit_violations.values()
                if current_time - timestamp < 3600  # Last hour
            ]
        )

        return {
            "status": "monitoring",
            "active_sources": active_sources,
            "total_sources_seen": len(self._source_stats),
            "recent_anomalies": dict(anomaly_counts),
            "total_anomalies": len(self._anomalies),
            "recent_rate_violations": recent_violations,
            "controller_address": f"{self._controller_addr:02X}",
            "uptime": current_time
            - min(
                (stats["first_seen"] for stats in self._source_stats.values()), default=current_time
            ),
        }

    def get_anomalies(
        self, since: float | None = None, severity: str | None = None
    ) -> list[Anomaly]:
        """
        Get anomalies matching criteria.

        Args:
            since: Timestamp to filter from (None for all)
            severity: Severity level to filter by (None for all)

        Returns:
            List of matching anomalies
        """
        anomalies = self._anomalies

        if since is not None:
            anomalies = [a for a in anomalies if a.timestamp >= since]

        if severity is not None:
            anomalies = [a for a in anomalies if a.severity == severity]

        return anomalies

    def get_source_statistics(self, source_address: int | None = None) -> dict[str, Any]:
        """
        Get statistics for source addresses.

        Args:
            source_address: Specific source to get stats for (None for all)

        Returns:
            Dictionary with source statistics
        """
        if source_address is not None:
            if source_address in self._source_stats:
                stats = self._source_stats[source_address].copy()
                stats["dgns_seen"] = list(stats["dgns_seen"])  # Convert set to list
                return {f"{source_address:02X}": stats}
            return {}

        # Return all source statistics
        result = {}
        for addr, stats in self._source_stats.items():
            addr_stats = stats.copy()
            addr_stats["dgns_seen"] = list(addr_stats["dgns_seen"])  # Convert set to list
            result[f"{addr:02X}"] = addr_stats

        return result

    def reset_statistics(self) -> None:
        """Reset all security statistics and tracking data."""
        self._message_counts.clear()
        self._dgn_counts.clear()
        self._source_stats.clear()
        self._rate_limit_violations.clear()
        self._anomalies.clear()

        logger.info("Security manager statistics reset")

    def update_rate_limits(self, limits: dict[str, RateLimit]) -> None:
        """
        Update rate limiting configuration.

        Args:
            limits: Dictionary of message type to RateLimit configuration
        """
        self._rate_limits.update(limits)
        logger.info(f"Rate limits updated: {list(limits.keys())}")

    def is_source_trusted(self, source_address: int) -> bool:
        """
        Check if a source address is considered trusted.

        Args:
            source_address: Source address to check

        Returns:
            True if trusted, False otherwise
        """
        # Our own controller is always trusted
        if source_address == self._controller_addr:
            return True

        # Check if source has a good track record
        if source_address in self._source_stats:
            stats = self._source_stats[source_address]

            # Consider trusted if:
            # - Low suspicious activity
            # - Been seen for a while
            # - Few rate violations
            return (
                stats["suspicious_activity"] < 5
                and time.time() - stats["first_seen"] > 300  # 5 minutes
                and stats["rate_violations"] < 3
            )

        # Unknown sources are not trusted initially
        return False
