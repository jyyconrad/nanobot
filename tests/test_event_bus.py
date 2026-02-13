"""Tests for event bus and service communication."""

import asyncio
import pytest
from nanobot.agents.event_bus import (
    Event,
    EventType,
    EventBus,
    EventListener,
    ServiceCommunicator
)


class TestEventBus:
    """Test suite for EventBus."""

    @pytest.mark.asyncio
    async def test_publish_event(self):
        """Test publishing an event."""
        bus = EventBus()

        event = await bus.publish(
            EventType.TASK_STARTED,
            "test-service",
            {"task_id": "123"}
        )

        assert event.event_type == EventType.TASK_STARTED
        assert event.source == "test-service"
        assert event.data["task_id"] == "123"

    @pytest.mark.asyncio
    async def test_subscribe_and_receive(self):
        """Test subscribing and receiving events."""
        bus = EventBus()
        received_events = []

        async def event_handler(event: Event):
            received_events.append(event)

        # Subscribe
        listener_id = await bus.subscribe(
            EventType.TASK_COMPLETED,
            event_handler
        )

        # Publish event
        await bus.publish(
            EventType.TASK_COMPLETED,
            "test-service",
            {"task_id": "123"}
        )

        # Wait for processing
        await asyncio.sleep(0.1)

        assert len(received_events) == 1
        assert received_events[0].data["task_id"] == "123"

    @pytest.mark.asyncio
    async def test_event_filtering(self):
        """Test event filtering."""
        bus = EventBus()
        received_events = []

        # Filter for only events with specific task_id
        def event_filter(event: Event) -> bool:
            return event.data.get("task_id") == "target"

        async def event_handler(event: Event):
            received_events.append(event)

        # Subscribe with filter
        await bus.subscribe(
            EventType.TASK_COMPLETED,
            event_handler,
            event_filter=event_filter
        )

        # Publish matching event
        await bus.publish(
            EventType.TASK_COMPLETED,
            "test-service",
            {"task_id": "target"}
        )

        # Publish non-matching event
        await bus.publish(
            EventType.TASK_COMPLETED,
            "test-service",
            {"task_id": "other"}
        )

        await asyncio.sleep(0.1)

        # Only matching event should be received
        assert len(received_events) == 1
        assert received_events[0].data["task_id"] == "target"

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        received_events = []

        async def event_handler(event: Event):
            received_events.append(event)

        # Subscribe
        listener_id = await bus.subscribe(
            EventType.TASK_STARTED,
            event_handler
        )

        # Publish one event
        await bus.publish(
            EventType.TASK_STARTED,
            "test-service",
            {"task_id": "1"}
        )

        await asyncio.sleep(0.1)
        assert len(received_events) == 1

        # Unsubscribe
        await bus.unsubscribe(EventType.TASK_STARTED, listener_id)

        # Publish another event
        await bus.publish(
            EventType.TASK_STARTED,
            "test-service",
            {"task_id": "2"}
        )

        await asyncio.sleep(0.1)
        # Should not receive second event
        assert len(received_events) == 1

    @pytest.mark.asyncio
    async def test_multiple_listeners(self):
        """Test multiple listeners for same event type."""
        bus = EventBus()
        received_1 = []
        received_2 = []

        async def handler1(event: Event):
            received_1.append(event)

        async def handler2(event: Event):
            received_2.append(event)

        # Subscribe two listeners
        await bus.subscribe(EventType.TASK_STARTED, handler1)
        await bus.subscribe(EventType.TASK_STARTED, handler2)

        # Publish
        await bus.publish(
            EventType.TASK_STARTED,
            "test-service",
            {"task_id": "123"}
        )

        await asyncio.sleep(0.1)

        # Both should receive
        assert len(received_1) == 1
        assert len(received_2) == 1

    @pytest.mark.asyncio
    async def test_event_history(self):
        """Test event history."""
        bus = EventBus(max_history=10)

        # Publish several events
        for i in range(5):
            await bus.publish(
                EventType.TASK_COMPLETED,
                "test-service",
                {"task_id": str(i)}
            )

        # Get history
        history = await bus.get_history(limit=10)

        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_history_filtering(self):
        """Test filtering event history."""
        bus = EventBus(max_history=100)

        # Publish events from different sources
        await bus.publish(
            EventType.TASK_COMPLETED,
            "service-a",
            {"task_id": "1"}
        )
        await bus.publish(
            EventType.TASK_COMPLETED,
            "service-b",
            {"task_id": "2"}
        )
        await bus.publish(
            EventType.TASK_STARTED,
            "service-a",
            {"task_id": "3"}
        )

        # Filter by source
        service_a_events = await bus.get_history(source="service-a")
        assert len(service_a_events) == 2

        # Filter by type
        completed_events = await bus.get_history(event_type=EventType.TASK_COMPLETED)
        assert len(completed_events) == 2

    @pytest.mark.asyncio
    async def test_stats(self):
        """Test statistics."""
        bus = EventBus()

        # Publish events
        for i in range(3):
            await bus.publish(
                EventType.TASK_COMPLETED,
                "test-service",
                {"task_id": str(i)}
            )

        # Wait for processing
        await asyncio.sleep(0.1)

        stats = bus.get_stats()
        assert stats["events_published"] == 3

    @pytest.mark.asyncio
    async def test_clear_history(self):
        """Test clearing event history."""
        bus = EventBus()

        await bus.publish(
            EventType.TASK_COMPLETED,
            "test-service",
            {"task_id": "1"}
        )

        history = await bus.get_history()
        assert len(history) == 1

        await bus.clear_history()

        history = await bus.get_history()
        assert len(history) == 0


class TestServiceCommunicator:
    """Test suite for ServiceCommunicator."""

    @pytest.mark.asyncio
    async def test_send_request(self):
        """Test sending a request to another service."""
        bus = EventBus()

        # Create services
        client = ServiceCommunicator("client-service", bus)
        server = ServiceCommunicator("server-service", bus)

        # Register handler on server
        async def handle_request(data):
            return {"result": data["value"] * 2}

        await server.handle_request("multiply", handle_request)

        # Send request from client
        response = await client.send_request(
            "server-service",
            "multiply",
            {"value": 21}
        )

        assert response is not None
        assert response["result"] == 42

        # Cleanup
        await client.cleanup()
        await server.cleanup()

    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """Test request timeout."""
        bus = EventBus()

        # Create client
        client = ServiceCommunicator("client-service", bus)

        # Send request to non-existent service
        response = await client.send_request(
            "non-existent-service",
            "test-request",
            {},
            timeout=1.0
        )

        # Should timeout and return None
        assert response is None

        # Cleanup
        await client.cleanup()

    @pytest.mark.asyncio
    async def test_broadcast_event(self):
        """Test broadcasting events."""
        bus = EventBus()

        service_a = ServiceCommunicator("service-a", bus)
        service_b = ServiceCommunicator("service-b", bus)

        received_events = []

        async def event_handler(event: Event):
            received_events.append(event)

        # Subscribe on service-b
        await bus.subscribe(EventType.STATUS_CHANGED, event_handler)

        # Broadcast from service-a
        await service_a.broadcast_event(
            EventType.STATUS_CHANGED,
            {"status": "ready"}
        )

        await asyncio.sleep(0.1)

        # Service-b should have received
        assert len(received_events) == 1
        assert received_events[0].data["status"] == "ready"

        # Cleanup
        await service_a.cleanup()
        await service_b.cleanup()

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup of subscriptions."""
        bus = EventBus()

        service = ServiceCommunicator("test-service", bus)

        # Register handler
        async def handler(data):
            return {}

        await service.handle_request("test", handler)

        # Cleanup
        await service.cleanup()

        # Send request - should not be handled
        response = await service.send_request(
            "test-service",
            "test",
            {},
            timeout=1.0
        )

        assert response is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
