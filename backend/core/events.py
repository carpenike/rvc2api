"""
Event system for asynchronous communication between components.

This module provides a simple event bus for publishing and subscribing to events,
helping to decouple components and break circular dependencies.
"""

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)

# Type aliases
EventHandler = Callable[[dict[str, Any]], None]
AsyncEventHandler = Callable[[dict[str, Any]], Awaitable[None]]
Handler = EventHandler | AsyncEventHandler

background_tasks: set = set()


class EventBus:
    """
    Simple publish-subscribe event bus for async communication.

    This class allows components to subscribe to events and publish events
    to subscribers, enabling decoupled communication between components.
    """

    def __init__(self):
        """Initialize the event bus with empty subscription maps."""
        self._subscribers: dict[str, set[Handler]] = {}
        self._once_subscribers: dict[str, set[Handler]] = {}

    def subscribe(self, event_type: str, handler: Handler) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to invoke when event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()

        self._subscribers[event_type].add(handler)
        logger.debug(f"Subscribed to event: {event_type}")

    def subscribe_once(self, event_type: str, handler: Handler) -> None:
        """
        Subscribe to an event type once.

        The handler will be automatically unsubscribed after the first event.

        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to invoke when event occurs
        """
        if event_type not in self._once_subscribers:
            self._once_subscribers[event_type] = set()

        self._once_subscribers[event_type].add(handler)

    def unsubscribe(self, event_type: str, handler: Handler) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove from subscribers
        """
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            logger.debug(f"Unsubscribed from event: {event_type}")

        if event_type in self._once_subscribers and handler in self._once_subscribers[event_type]:
            self._once_subscribers[event_type].remove(handler)

    def publish(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """
        Publish an event synchronously.

        This is a convenience method that calls publish_async in the background.
        For most use cases, using publish_async directly is preferred.

        Args:
            event_type: Type of event to publish
            data: Event payload data (optional)
        """
        if asyncio.get_event_loop().is_running():
            if not hasattr(self, "_background_tasks"):
                self._background_tasks = set()
            task = asyncio.create_task(self.publish_async(event_type, data or {}))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        else:
            # This should generally be avoided - events should be published in an async context
            logger.warning(f"Publishing event {event_type} outside of an event loop")
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self.publish_async(event_type, data or {}))
            finally:
                loop.close()

    async def publish_async(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """
        Publish an event asynchronously.

        Args:
            event_type: Type of event to publish
            data: Event payload data (optional)
        """
        if data is None:
            data = {}

        # Add event type to data for convenience
        data["event_type"] = event_type

        # Get regular subscribers
        regular_handlers = self._subscribers.get(event_type, set())

        # Get once-only subscribers and clear them
        once_handlers = self._once_subscribers.get(event_type, set())
        if once_handlers:
            self._once_subscribers[event_type] = set()

        # Combine handlers
        all_handlers = regular_handlers.union(once_handlers)

        if not all_handlers:
            logger.debug(f"No subscribers for event: {event_type}")
            return

        logger.debug(f"Publishing event: {event_type} to {len(all_handlers)} subscribers")

        # Call all handlers
        for handler in all_handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    # Async handler
                    await handler(data)
                else:
                    # Sync handler - run in executor to avoid blocking
                    await asyncio.to_thread(handler, data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")

    def publish_later(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """
        Publish an event in the background.

        Args:
            event_type: Type of event to publish
            data: Event payload data (optional)
        """
        if not hasattr(self, "_background_tasks"):
            self._background_tasks = set()
        task = asyncio.create_task(self.publish_async(event_type, data or {}))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)


# Global instance for singleton access
_event_bus: EventBus = EventBus()


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.

    Returns:
        Singleton EventBus instance
    """
    return _event_bus
