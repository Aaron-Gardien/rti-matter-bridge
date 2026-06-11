#!/usr/bin/env python3
"""Generate RTI switch configuration from imported Apex variables.

The generator validates that every switch feedback variable exists in the
mapping produced by apex_variable_importer.py. Macro names must be supplied from
real RTI programming data or user selection; the tool does not invent them.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def variables_by_id(apex_mapping: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for item in apex_mapping.get("variables", []):
        variable_id = item.get("id")
        if variable_id is not None:
            result[int(variable_id)] = item
    return result


def build_selection_template(apex_mapping: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_apex": apex_mapping.get("source_apex"),
        "variables": apex_mapping.get("variables", []),
        "switches": [],
    }


def build_switch_config(apex_mapping: dict[str, Any], switch_selection: dict[str, Any]) -> dict[str, Any]:
    variable_index = variables_by_id(apex_mapping)
    switches: list[dict[str, Any]] = []

    for item in switch_selection.get("switches", []):
        switch_id = str(item.get("id") or "").strip()
        if not switch_id:
            raise ValueError("Every switch requires an id")

        on_macro = str(item.get("on_macro") or "").strip()
        off_macro = str(item.get("off_macro") or "").strip()
        if not on_macro or not off_macro:
            raise ValueError(f"Switch {switch_id} requires on_macro and off_macro")

        feedback_variable_id = item.get("feedback_variable_id")
        if feedback_variable_id is None:
            raise ValueError(f"Switch {switch_id} requires feedback_variable_id")

        feedback_variable = variable_index.get(int(feedback_variable_id))
        if not feedback_variable:
            raise ValueError(f"Switch {switch_id} feedback variable {feedback_variable_id} is not in the Apex mapping")

        feedback = {
            "variable_id": int(feedback_variable_id),
            "sysvar": feedback_variable.get("sysvar"),
            "name": feedback_variable.get("name"),
            "on_values": item.get("on_values", ["1", "true", "on", "active", "yes"]),
            "off_values": item.get("off_values", ["0", "false", "off", "inactive", "no", "null", ""]),
        }

        switches.append(
            {
                "id": switch_id,
                "name": item.get("name") or switch_id,
                "on_macro": on_macro,
                "off_macro": off_macro,
                "feedback": feedback,
            }
        )

    return {
        "source_apex": apex_mapping.get("source_apex"),
        "switches": switches,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate RTI Matterbridge switch config from Apex variable mapping.")
    parser.add_argument("--apex-mapping", type=Path, required=True, help="Mapping JSON from apex_variable_importer.py.")
    parser.add_argument("--switch-selection", type=Path, help="JSON file listing selected switches and macro names.")
    parser.add_argument("--output", type=Path, default=Path("rti_switches.json"), help="Runtime switch config output path.")
    parser.add_argument("--write-template", type=Path, help="Write a selection template containing discovered variables.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    apex_mapping = load_json(args.apex_mapping)

    if args.write_template:
        write_json(args.write_template, build_selection_template(apex_mapping))
        print(f"Wrote switch selection template: {args.write_template}")

    if args.switch_selection:
        switch_selection = load_json(args.switch_selection)
        config = build_switch_config(apex_mapping, switch_selection)
        write_json(args.output, config)
        print(f"Wrote switch config: {args.output}")
        print(f"Switches configured: {len(config['switches'])}")
    elif not args.write_template:
        raise SystemExit("Provide --switch-selection to generate config, or --write-template to create a selection file.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
