#!/usr/bin/env python3
"""RTI activity switch mapping for Matterbridge.

Each switch maps a Matter on/off command to an RTI macro name and maps one RTI
system variable subscription back to switch state feedback.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_ON_VALUES = frozenset({"1", "true", "on", "active", "yes"})
DEFAULT_OFF_VALUES = frozenset({"0", "false", "off", "inactive", "no", "null", ""})


@dataclass(frozen=True)
class SwitchFeedback:
    variable_id: int
    sysvar: str | None = None
    name: str | None = None
    on_values: frozenset[str] = DEFAULT_ON_VALUES
    off_values: frozenset[str] = DEFAULT_OFF_VALUES

    def state_for_value(self, value: Any) -> bool | None:
        normalized = "" if value is None else str(value).strip().lower()
        if normalized in self.on_values:
            return True
        if normalized in self.off_values:
            return False
        return None


@dataclass(frozen=True)
class RtiSwitch:
    id: str
    name: str
    on_macro: str
    off_macro: str
    feedback: SwitchFeedback
    metadata: dict[str, Any] = field(default_factory=dict)

    def macro_for_command(self, command: str) -> str | None:
        normalized = command.strip().lower()
        if normalized in {"on", "turn_on", "true"}:
            return self.on_macro
        if normalized in {"off", "turn_off", "false"}:
            return self.off_macro
        return None


def _as_string_set(values: list[Any] | None, defaults: frozenset[str]) -> frozenset[str]:
    if not values:
        return defaults
    return frozenset(str(value).strip().lower() for value in values)


def load_switch_config(path: str | Path) -> dict[str, RtiSwitch]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    switches: dict[str, RtiSwitch] = {}
    for item in payload.get("switches", []):
        feedback = item.get("feedback", {})
        variable_id = feedback.get("variable_id")
        if variable_id is None:
            raise ValueError(f"Switch {item.get('id', '<unknown>')} is missing feedback.variable_id")

        switch_id = str(item.get("id") or "").strip()
        if not switch_id:
            raise ValueError("Switch id is required")

        switch = RtiSwitch(
            id=switch_id,
            name=str(item.get("name") or switch_id),
            on_macro=str(item["on_macro"]),
            off_macro=str(item["off_macro"]),
            feedback=SwitchFeedback(
                variable_id=int(variable_id),
                sysvar=feedback.get("sysvar"),
                name=feedback.get("name"),
                on_values=_as_string_set(feedback.get("on_values"), DEFAULT_ON_VALUES),
                off_values=_as_string_set(feedback.get("off_values"), DEFAULT_OFF_VALUES),
            ),
            metadata={key: value for key, value in item.items() if key not in {"id", "name", "on_macro", "off_macro", "feedback"}},
        )
        switches[switch.id] = switch

    return switches


class RtiSwitchPlugin:
    def __init__(self, switches: dict[str, RtiSwitch]):
        self.switches = switches
        self.feedback_index = {switch.feedback.variable_id: switch for switch in switches.values()}
        self.states: dict[str, bool] = {}

    @classmethod
    def from_file(cls, path: str | Path) -> "RtiSwitchPlugin":
        return cls(load_switch_config(path))

    def tracked_variable_ids(self) -> list[int]:
        return sorted(self.feedback_index)

    def macro_for_command(self, device_id: str, command: str) -> str | None:
        switch = self.switches.get(device_id)
        return switch.macro_for_command(command) if switch else None

    def handle_feedback(self, variable_id: int, value: Any) -> dict[str, Any] | None:
        switch = self.feedback_index.get(int(variable_id))
        if not switch:
            return None

        state = switch.feedback.state_for_value(value)
        if state is None:
            return None

        self.states[switch.id] = state
        return {
            "device_id": switch.id,
            "device_name": switch.name,
            "device_type": "switch",
            "state": {"on": state},
            "feedback_variable_id": switch.feedback.variable_id,
            "feedback_sysvar": switch.feedback.sysvar,
            "feedback_value": value,
        }
