# core/event_bus.py
from collections import defaultdict
from typing import Any, Callable, Dict, List, Type


class EventBus:
    """
    Simple synchronous event bus.
    Handlers are invoked immediately when an event is published.
    """

    def __init__(self) -> None:
        self._handlers: Dict[Type, List[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: Type, handler: Callable[[Any], None]) -> None:
        """Register a handler for a specific event type."""
        self._handlers[event_type].append(handler)

    def publish(self, event: Any) -> None:
        """Invoke all handlers subscribed to the event's type."""
        for handler in self._handlers.get(type(event), []):
            handler(event)


# Global event bus instance
event_bus = EventBus()
