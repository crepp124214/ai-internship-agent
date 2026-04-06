from datetime import datetime, timezone
from typing import NamedTuple


class StateTransition(NamedTuple):
    from_state: str
    to_state: str
    timestamp: datetime
    reason: str | None


class StateMachine:
    """
    Agent 执行状态机
    状态：idle | planning | tool_use | responding | done
    """

    VALID_TRANSITIONS = {
        "idle": {"planning"},
        "planning": {"tool_use", "responding", "done"},
        "tool_use": {"planning", "responding", "done"},
        "responding": {"done", "planning"},
        "done": {"idle"},
    }

    ALL_STATES = {"idle", "planning", "tool_use", "responding", "done"}

    def __init__(self) -> None:
        self._state = "idle"
        self._history: list[StateTransition] = []

    def transition(self, to: str, reason: str | None = None) -> None:
        if to not in self.ALL_STATES:
            raise ValueError(f"Unknown state: {to}")
        allowed = self.VALID_TRANSITIONS.get(self._state, set())
        if to not in allowed:
            raise ValueError(
                f"Invalid transition from '{self._state}' to '{to}'. "
                f"Allowed: {allowed or 'none'}"
            )
        self._history.append(StateTransition(
            from_state=self._state,
            to_state=to,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
        ))
        self._state = to

    def get_state(self) -> str:
        return self._state

    def get_history(self) -> list[StateTransition]:
        return list(self._history)

    def reset(self) -> None:
        self._state = "idle"
        self._history.clear()
