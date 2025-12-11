# core/event_bus.py
from collections import defaultdict
from typing import Any, Callable, Dict, List, Type


class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[Type, List[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: Type, handler: Callable[[Any], None]) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: Any) -> None:
        """
        Синхронно вызывает всех подписчиков для данного типа события.
        """
        for handler in self._handlers.get(type(event), []):
            handler(event)


# Глобальный bus для проекта
event_bus = EventBus()
