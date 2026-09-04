from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypeVar

from app.agent.state import AgentState

T = TypeVar("T")


def add_trace(state: AgentState, node: str, details: str, status: str = "completed") -> list[dict[str, Any]]:
    return [*state.get("execution_trace", []), {"node": node, "status": status, "details": details}]


def timed(state: AgentState, name: str, operation: Callable[[], T]) -> tuple[T, dict[str, float]]:
    started = time.perf_counter()
    result = operation()
    elapsed = time.perf_counter() - started
    return result, {**state.get("timings", {}), name: round(elapsed, 6)}

