import pytest
from src.core.runtime.state_machine import StateMachine, StateTransition


def test_initial_state_is_idle():
    sm = StateMachine()
    assert sm.get_state() == "idle"


def test_valid_transition_idle_to_planning():
    sm = StateMachine()
    sm.transition("planning")
    assert sm.get_state() == "planning"


def test_invalid_transition_raises():
    sm = StateMachine()
    with pytest.raises(ValueError):
        sm.transition("done")  # idle cannot go directly to done


def test_history_records_transitions():
    sm = StateMachine()
    sm.transition("planning", reason="starting task")
    history = sm.get_history()
    assert len(history) == 1
    assert history[0].from_state == "idle"
    assert history[0].to_state == "planning"
    assert history[0].reason == "starting task"


def test_reset_returns_to_idle():
    sm = StateMachine()
    sm.transition("planning")
    sm.reset()
    assert sm.get_state() == "idle"
