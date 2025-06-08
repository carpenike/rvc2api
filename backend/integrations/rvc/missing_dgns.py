"""
Missing DGN tracking for RV-C decoding.

This module tracks DGNs (Data Group Numbers) that are encountered but not
found in the RVC specification, allowing for analysis and future updates.
"""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class MissingDGNTracker:
    """
    Tracks missing DGNs encountered during decoding.

    This helps identify gaps in the RVC specification coverage and
    can be used to prioritize specification updates.
    """

    def __init__(self):
        """Initialize the missing DGN tracker."""
        self._missing_dgns: dict[int, dict[str, Any]] = {}
        self._lock = None  # Will use asyncio.Lock if needed in async context

    def record_missing_dgn(
        self, dgn_id: int, can_id: int | None = None, context: str | None = None
    ) -> None:
        """
        Record a missing DGN for future processing.

        Args:
            dgn_id: The DGN ID that was not found in the specification
            can_id: Optional CAN ID where this DGN was encountered
            context: Optional context string describing where/how this was encountered
        """
        if dgn_id not in self._missing_dgns:
            self._missing_dgns[dgn_id] = {
                "dgn_id": dgn_id,
                "dgn_hex": f"{dgn_id:X}",
                "first_seen": time.time(),
                "last_seen": time.time(),
                "encounter_count": 0,
                "can_ids": set(),
                "contexts": set(),
                "pgn": dgn_id & 0x3FFFF,  # Extract PGN from DGN
                "priority": (dgn_id >> 18) & 0x7,  # Extract priority
            }

        entry = self._missing_dgns[dgn_id]
        entry["encounter_count"] += 1
        entry["last_seen"] = time.time()

        if can_id is not None:
            entry["can_ids"].add(can_id)

        if context:
            entry["contexts"].add(context)

        # Log periodically (every 10 encounters)
        if entry["encounter_count"] % 10 == 1:
            logger.debug(
                f"Missing DGN recorded: {dgn_id:X} "
                f"(PGN: {entry['pgn']:X}, count: {entry['encounter_count']})"
            )

    def get_missing_dgns(self) -> dict[int, dict[str, Any]]:
        """
        Get the current storage of missing DGNs.

        Returns:
            Dictionary mapping DGN IDs to metadata about when/how they were encountered
        """
        # Convert sets to lists for JSON serialization
        result = {}
        for dgn_id, entry in self._missing_dgns.items():
            entry_copy = entry.copy()
            entry_copy["can_ids"] = list(entry["can_ids"])
            entry_copy["contexts"] = list(entry["contexts"])
            result[dgn_id] = entry_copy

        return result

    def get_summary(self) -> dict[str, Any]:
        """
        Get a summary of missing DGNs.

        Returns:
            Summary statistics about missing DGNs
        """
        if not self._missing_dgns:
            return {
                "total_missing": 0,
                "most_frequent": [],
                "recently_seen": [],
            }

        # Sort by encounter count
        by_count = sorted(
            self._missing_dgns.items(), key=lambda x: x[1]["encounter_count"], reverse=True
        )

        # Sort by last seen time
        by_time = sorted(self._missing_dgns.items(), key=lambda x: x[1]["last_seen"], reverse=True)

        return {
            "total_missing": len(self._missing_dgns),
            "total_encounters": sum(e["encounter_count"] for e in self._missing_dgns.values()),
            "most_frequent": [
                {
                    "dgn_hex": entry["dgn_hex"],
                    "pgn_hex": f"{entry['pgn']:X}",
                    "count": entry["encounter_count"],
                    "priority": entry["priority"],
                }
                for _, entry in by_count[:10]
            ],
            "recently_seen": [
                {
                    "dgn_hex": entry["dgn_hex"],
                    "pgn_hex": f"{entry['pgn']:X}",
                    "last_seen": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(entry["last_seen"])
                    ),
                }
                for _, entry in by_time[:10]
            ],
        }

    def clear(self) -> None:
        """Clear the missing DGNs storage."""
        self._missing_dgns.clear()
        logger.debug("Missing DGN storage cleared")

    def export_for_analysis(self) -> list[dict[str, Any]]:
        """
        Export missing DGNs in a format suitable for analysis.

        Returns:
            List of missing DGN entries sorted by frequency
        """
        entries = []

        for dgn_id, entry in self._missing_dgns.items():
            entries.append(
                {
                    "dgn_id": dgn_id,
                    "dgn_hex": entry["dgn_hex"],
                    "pgn": entry["pgn"],
                    "pgn_hex": f"{entry['pgn']:X}",
                    "priority": entry["priority"],
                    "encounter_count": entry["encounter_count"],
                    "first_seen": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(entry["first_seen"])
                    ),
                    "last_seen": time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(entry["last_seen"])
                    ),
                    "can_ids": list(entry["can_ids"]),
                    "contexts": list(entry["contexts"]),
                }
            )

        # Sort by encounter count (most frequent first)
        entries.sort(key=lambda x: x["encounter_count"], reverse=True)

        return entries


# Global instance for backward compatibility
_global_tracker = MissingDGNTracker()


def record_missing_dgn(dgn_id: int, can_id: int | None = None, context: str | None = None) -> None:
    """
    Record a missing DGN using the global tracker.

    This function maintains backward compatibility with the existing API.
    """
    _global_tracker.record_missing_dgn(dgn_id, can_id, context)


def get_missing_dgns() -> dict[int, dict[str, Any]]:
    """Get missing DGNs from the global tracker."""
    return _global_tracker.get_missing_dgns()


def clear_missing_dgns() -> None:
    """Clear the global tracker."""
    _global_tracker.clear()
