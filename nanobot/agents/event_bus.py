"""Event-driven communication system for service communication."""

import asyncio
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from loguru import logger


class EventType(Enum):
    """Event type categories."""

    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    STATUS_CHANGED = "status_changed"
    RESOURCE_UPDATED = "resource_updated"
    ERROR_OCCURRED = "error_occurred"
    CUSTOM = "custom"


@dataclass
class Event:
    """Represents an event in the system."""

    event_id: str
    event_type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: float
    metadata: Dict[str, Any]

    @classmethod
    def create(
        cls,
        event_type: EventType,
        source: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Event":
        """Create a new event."""
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source=source,
            data=data,
            timestamp=time.time(),
            metadata=metadata or {},
        )


class EventListener:
    """Event listener with filtering capabilities."""

    def __init__(
        self,
        listener_id: str,
        callback: Callable[[Event], Any],
        event_filter: Optional[Callable[[Event], bool]] = None,
    ):
        """
        Initialize event listener.

        Args:
            listener_id: Unique listener identifier
            callback: Async function to call when event matches
            event_filter: Optional filter function
        """
        self.listener_id = listener_id
        self.callback = callback
        self.event_filter = event_filter

    async def process(self, event: Event) -> bool:
        """
        Process an event.

        Args:
            event: Event to process

        Returns:
            True if event was processed, False if filtered
        """
        if self.event_filter and not self.event_filter(event):
            return False

        try:
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(event)
            else:
                self.callback(event)
            return True
        except Exception as e:
            logger.error(f"Error in listener {self.listener_id}: {e}")
            return False


class EventBus:
    """
    Event-driven communication system.

    Features:
    - Pub/sub event model
    - Event filtering
    - Async event processing
    - Event history
    - Performance monitoring
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize event bus.

        Args:
            max_history: Maximum number of events to keep in history
        """
        self.max_history = max_history
        self._listeners: Dict[EventType, List[EventListener]] = {}
        self._listeners_lock = asyncio.Lock()
        self._event_history: List[Event] = []
        self._history_lock = asyncio.Lock()
        self._stats: Dict[str, Any] = {
            "events_published": 0,
            "events_processed": 0,
            "events_filtered": 0,
            "errors": 0,
        }

    async def publish(
        self,
        event_type: EventType,
        source: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """
        Publish an event.

        Args:
            event_type: Event type
            source: Event source
            data: Event data
            metadata: Optional metadata

        Returns:
            Published event
        """
        # Create event
        event = Event.create(event_type, source, data, metadata)

        # Add to history
        await self._add_to_history(event)

        # Update stats
        self._stats["events_published"] += 1

        # Notify listeners
        await self._notify_listeners(event)

        logger.debug(f"Event published: {event_type.value} from {source}")
        return event

    async def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], Any],
        event_filter: Optional[Callable[[Event], bool]] = None,
    ) -> str:
        """
        Subscribe to events.

        Args:
            event_type: Event type to subscribe to
            callback: Callback function
            event_filter: Optional event filter

        Returns:
            Listener ID
        """
        listener_id = str(uuid.uuid4())
        listener = EventListener(listener_id, callback, event_filter)

        async with self._listeners_lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(listener)

        logger.debug(f"Subscribed to {event_type.value}: {listener_id}")
        return listener_id

    async def unsubscribe(self, event_type: EventType, listener_id: str) -> bool:
        """
        Unsubscribe from events.

        Args:
            event_type: Event type
            listener_id: Listener ID

        Returns:
            True if unsubscribed, False if not found
        """
        async with self._listeners_lock:
            if event_type not in self._listeners:
                return False

            self._listeners[event_type] = [
                l for l in self._listeners[event_type] if l.listener_id != listener_id
            ]

            logger.debug(f"Unsubscribed from {event_type.value}: {listener_id}")
            return True

    async def _notify_listeners(self, event: Event):
        """Notify all listeners of an event."""
        async with self._listeners_lock:
            listeners = self._listeners.get(event.event_type, []).copy()

        # Process listeners concurrently
        tasks = [listener.process(event) for listener in listeners]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Update stats
        for result in results:
            if isinstance(result, Exception):
                self._stats["errors"] += 1
            elif result is True:
                self._stats["events_processed"] += 1
            else:
                self._stats["events_filtered"] += 1

    async def _add_to_history(self, event: Event):
        """Add event to history."""
        async with self._history_lock:
            self._event_history.append(event)

            # Trim history if needed
            if len(self._event_history) > self.max_history:
                self._event_history = self._event_history[-self.max_history :]

    async def get_history(
        self,
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        limit: int = 100,
        since: Optional[float] = None,
    ) -> List[Event]:
        """
        Get event history.

        Args:
            event_type: Filter by event type
            source: Filter by source
            limit: Maximum number of events
            since: Only events after this timestamp

        Returns:
            List of events
        """
        async with self._history_lock:
            events = self._event_history.copy()

        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if source:
            events = [e for e in events if e.source == source]

        if since:
            events = [e for e in events if e.timestamp >= since]

        # Sort by timestamp (most recent first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        # Limit
        return events[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return self._stats.copy()

    async def clear_history(self):
        """Clear event history."""
        async with self._history_lock:
            self._event_history.clear()

        logger.info("Event history cleared")


class ServiceCommunicator:
    """
    Service-to-service communication via event bus.

    Provides high-level abstractions for service communication.
    """

    def __init__(self, service_name: str, event_bus: EventBus):
        """
        Initialize service communicator.

        Args:
            service_name: Name of this service
            event_bus: Event bus instance
        """
        self.service_name = service_name
        self._event_bus = event_bus
        self._subscriptions: Dict[str, str] = {}  # event_type -> listener_id

    async def send_request(
        self,
        target_service: str,
        request_type: str,
        data: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Send a request to another service.

        Args:
            target_service: Target service name
            request_type: Type of request
            data: Request data
            timeout: Request timeout

        Returns:
            Response data or None if timeout
        """
        request_id = str(uuid.uuid4())

        # Create request event
        await self._event_bus.publish(
            EventType.CUSTOM,
            self.service_name,
            {
                "type": "request",
                "request_type": request_type,
                "request_id": request_id,
                "target": target_service,
                "data": data,
            },
        )

        # Wait for response
        response_received = asyncio.Event()
        response_data: Optional[Dict[str, Any]] = None

        async def response_handler(event: Event):
            nonlocal response_data
            if (
                event.data.get("type") == "response"
                and event.data.get("request_id") == request_id
            ):
                response_data = event.data.get("data")
                response_received.set()

        # Subscribe to responses
        listener_id = await self._event_bus.subscribe(
            EventType.CUSTOM, response_handler
        )

        try:
            # Wait for response
            await asyncio.wait_for(response_received.wait(), timeout=timeout)
            return response_data
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout: {request_id}")
            return None
        finally:
            await self._event_bus.unsubscribe(EventType.CUSTOM, listener_id)

    async def handle_request(
        self, request_type: str, handler: Callable[[Dict[str, Any]], Dict[str, Any]]
    ):
        """
        Register a request handler.

        Args:
            request_type: Request type to handle
            handler: Handler function
        """

        async def request_handler(event: Event):
            if (
                event.data.get("type") == "request"
                and event.data.get("request_type") == request_type
                and event.data.get("target") == self.service_name
            ):
                request_id = event.data.get("request_id")
                request_data = event.data.get("data", {})

                try:
                    # Process request
                    response_data = await handler(request_data)

                    # Send response
                    await self._event_bus.publish(
                        EventType.CUSTOM,
                        self.service_name,
                        {
                            "type": "response",
                            "request_id": request_id,
                            "data": response_data,
                        },
                    )

                except Exception as e:
                    logger.error(f"Error handling request {request_type}: {e}")

        # Subscribe to requests
        listener_id = await self._event_bus.subscribe(EventType.CUSTOM, request_handler)

        self._subscriptions[request_type] = listener_id
        logger.debug(f"Registered handler for {request_type}")

    async def broadcast_event(self, event_type: EventType, data: Dict[str, Any]):
        """
        Broadcast an event to all services.

        Args:
            event_type: Event type
            data: Event data
        """
        await self._event_bus.publish(event_type, self.service_name, data)

    async def cleanup(self):
        """Clean up subscriptions."""
        for event_type_str, listener_id in self._subscriptions.items():
            try:
                event_type = EventType(event_type_str)
                await self._event_bus.unsubscribe(event_type, listener_id)
            except ValueError:
                pass

        self._subscriptions.clear()
        logger.info(f"Service communicator cleaned up: {self.service_name}")
