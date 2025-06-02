"""
Testing utilities and fixtures for performance-related tests.
"""

import time

import pytest


class PerformanceTimer:
    """
    A simple timer utility for measuring code performance.
    Use this in tests to ensure operations complete within time constraints.
    """

    def __init__(self) -> None:
        """Initialize the performance timer."""
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.elapsed: float = 0

    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.time()

    def stop(self) -> float:
        """
        Stop the timer and return elapsed time.

        Returns:
            float: Elapsed time in seconds
        """
        if self.start_time is None:
            raise ValueError("Timer was not started")

        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        return self.elapsed

    def reset(self) -> None:
        """Reset the timer."""
        self.start_time = None
        self.end_time = None
        self.elapsed = 0


@pytest.fixture
def performance_timer() -> PerformanceTimer:
    """
    Fixture that provides a performance timer for measuring code execution time.

    Returns:
        PerformanceTimer: A timer utility instance
    """
    return PerformanceTimer()
