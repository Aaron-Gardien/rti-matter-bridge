#!/usr/bin/env python3
"""Import RTI Apex project variables into the Matterbridge driver package.

The RTI processor cannot create driver sysvars at runtime. This tool runs before
packaging/deploying the driver, extracts system variable references from an
`.apex` project export, and writes driver-ready `DiscoveredVar###` definitions.
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
from xml.dom import minidom
from xml.etree import ElementTree as ET


VARIABLE_ID_RE = re.compile(
    r"\b(?:sys(?:tem)?(?:var(?:iable)?)?|variable)[_\s-]*(?:id)?\s*[:=]\s*['\"]?(\d{1,6})\b",
    re.IGNORECASE,
)
PLAIN_VARIABLE_RE = re.compile(
    r"\b(?:sys(?:tem)?(?:var(?:iable)?)?|variable)\s+(\d{1,6})\b",
    re.IGNORECASE,
)
VARIABLE_WORDS = ("variable", "sysvar", "systemvariable", "system variable")
DEVICE_WORDS = ("device", "keypad", "light", "switch", "dimmer", "thermostat", "sensor")


@dataclass
class TrackedVariable:
    """A variable discovered in an Apex export."""

    id: int
    name: str
    type: str = "string"
    source: str = ""
    device: str = ""
    contexts: list[str] = field(default_factory=list)

    @property
    def sysvar(self) -> str:
        return f"DiscoveredVar{self.id:03d}"


def normalize_type(value: str | None) -> str:
    if not value:
        return "string"

    lowered = value.strip().lower()
    if lowered in {"bool", "boolean", "toggle"}:
        return "boolean"
    if lowered in {"int", "integer", "number", "percent", "percentage", "level"}:
        return "integer"
    return "string"


def safe_name(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    collapsed = " ".join(str(value).split())
    return collapsed or fallback


def read_apex_members(apex_path: Path) -> list[tuple[str, bytes]]:
    if not apex_path.exists():
        raise FileNotFoundError(f"Apex file not found: {apex_path}")

    if zipfile.is_zipfile(apex_path):
        members: list[tuple[str, bytes]] = []
        with zipfile.ZipFile(apex_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                suffix = Path(info.filename).suffix.lower()
                if suffix in {".xml", ".json", ".txt", ".apex"}:
                    members.append((info.filename, archive.read(info)))
        return members

    return [(apex_path.name, apex_path.read_bytes())]


def merge_variable(existing: TrackedVariable | None, incoming: TrackedVariable) -> TrackedVariable:
    if existing is None:
        return incoming

    if existing.name == f"Variable {existing.id}" and incoming.name != f"Variable {incoming.id}":
        existing.name = incoming.name
    if existing.type == "string" and incoming.type != "string":
        existing.type = incoming.type
    if not existing.device and incoming.device:
        existing.device = incoming.device
    if incoming.source and incoming.source not in existing.source.split(", "):
        existing.source = ", ".join(filter(None, [existing.source, incoming.source]))
    for context in incoming.contexts:
        if context not in existing.contexts:
            existing.contexts.append(context)
    return existing


def extract_variables_from_xml(member_name: str, data: bytes) -> Iterable[TrackedVariable]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return []

    variables: list[TrackedVariable] = []

    def walk(element: ET.Element, context: list[str]) -> None:
        attrs = {key.lower(): value for key, value in element.attrib.items()}
        tag = element.tag.split("}")[-1].lower()
        next_context = context[:]

        label = attrs.get("name") or attrs.get("label") or attrs.get("displayname")
        if label and any(word in tag or word in label.lower() for word in DEVICE_WORDS):
            next_context.append(safe_name(label, ""))

        id_value = first_int(
            attrs.get("id"),
            attrs.get("variableid"),
            attrs.get("sysvarid"),
            attrs.get("systemvariableid"),
            attrs.get("sysvar"),
        )
        looks_variable = any(word in tag for word in VARIABLE_WORDS) or any(
            word.replace(" ", "") in key for key in attrs for word in VARIABLE_WORDS
        )

        if id_value is not None and looks_variable:
            name = safe_name(
                attrs.get("name") or attrs.get("label") or attrs.get("displayname"),
                f"Variable {id_value}",
            )
            variables.append(
                TrackedVariable(
                    id=id_value,
                    name=name,
                    type=normalize_type(attrs.get("type") or attrs.get("datatype") or attrs.get("format")),
                    source=member_name,
                    device=next_context[-1] if next_context else "",
                    contexts=next_context,
                )
            )

        for child in list(element):
            walk(child, next_context)

    walk(root, [])
    return variables


def first_int(*values: Any) -> int | None:
    for value in values:
        if value is None:
            continue
        match = re.search(r"\d{1,6}", str(value))
        if match:
            return int(match.group(0))
    return None


def extract_variables_from_json(member_name: str, data: bytes) -> Iterable[TrackedVariable]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []

    variables: list[TrackedVariable] = []

    def walk(value: Any, context: list[str]) -> None:
        if isinstance(value, dict):
            lowered = {str(key).lower(): item for key, item in value.items()}
            label = lowered.get("name") or lowered.get("label") or lowered.get("displayname")
            next_context = context[:]
            if isinstance(label, str) and any(word in label.lower() for word in DEVICE_WORDS):
                next_context.append(safe_name(label, ""))

            id_value = first_int(
                lowered.get("id"),
                lowered.get("variableid"),
                lowered.get("sysvarid"),
                lowered.get("systemvariableid"),
            )
            looks_variable = any(key in lowered for key in ("variableid", "sysvarid", "systemvariableid")) or any(
                "variable" in str(key).lower() or "sysvar" in str(key).lower() for key in value
            )
            if id_value is not None and looks_variable:
                name = safe_name(label if isinstance(label, str) else None, f"Variable {id_value}")
                variables.append(
                    TrackedVariable(
                        id=id_value,
                        name=name,
                        type=normalize_type(str(lowered.get("type") or lowered.get("datatype") or "")),
                        source=member_name,
                        device=next_context[-1] if next_context else "",
                        contexts=next_context,
                    )
                )

            for child in value.values():
                walk(child, next_context)
        elif isinstance(value, list):
            for child in value:
                walk(child, context)
        elif isinstance(value, str):
            variables.extend(extract_variables_from_text(member_name, value))

    walk(payload, [])
    return variables


def extract_variables_from_text(member_name: str, text: str) -> Iterable[TrackedVariable]:
    variables: list[TrackedVariable] = []
    for regex in (VARIABLE_ID_RE, PLAIN_VARIABLE_RE):
        for match in regex.finditer(text):
            variable_id = int(match.group(1))
            variables.append(
                TrackedVariable(
                    id=variable_id,
                    name=f"Variable {variable_id}",
                    source=member_name,
                )
            )
    return variables


def extract_apex_variables(apex_path: Path) -> list[TrackedVariable]:
    by_id: dict[int, TrackedVariable] = {}

    for member_name, data in read_apex_members(apex_path):
        suffix = Path(member_name).suffix.lower()
        candidates: list[TrackedVariable] = []
        if suffix == ".json":
            candidates.extend(extract_variables_from_json(member_name, data))
        else:
            candidates.extend(extract_variables_from_xml(member_name, data))
            try:
                candidates.extend(extract_variables_from_text(member_name, data.decode("utf-8", errors="ignore")))
            except UnicodeDecodeError:
                pass

        for variable in candidates:
            by_id[variable.id] = merge_variable(by_id.get(variable.id), variable)

    return [by_id[key] for key in sorted(by_id)]


def build_mapping(apex_path: Path, variables: list[TrackedVariable]) -> dict[str, Any]:
    return {
        "source_apex": str(apex_path),
        "variables": [asdict(variable) | {"sysvar": variable.sysvar} for variable in variables],
    }


def variable_element(parent: ET.Element, variable: TrackedVariable) -> None:
    attrs = {
        "name": variable.name,
        "sysvar": variable.sysvar,
        "type": variable.type,
        "sample": "false" if variable.type == "boolean" else "",
    }
    if variable.type == "boolean":
        attrs["format"] = "B:Off:On"
    elif variable.type == "integer":
        attrs["min"] = "0"
        attrs["max"] = "100"

    ET.SubElement(parent, "variable", attrs)


def build_system_variables_xml(variables: list[TrackedVariable]) -> str:
    root = ET.Element("variables")

    connection = ET.SubElement(root, "category", {"name": "Connection State"})
    ET.SubElement(connection, "variable", {"name": "Connection State", "sysvar": "ConnectionState", "type": "integer", "sample": "0", "format": "L:0:Disconnected:1:Connected"})
    ET.SubElement(connection, "variable", {"name": "Disconnected", "sysvar": "ConnectionState00", "type": "boolean", "sample": "false", "format": "B:Off:On"})
    ET.SubElement(connection, "variable", {"name": "Connected", "sysvar": "ConnectionState01", "type": "boolean", "sample": "true", "format": "B:Off:On"})

    system = ET.SubElement(root, "category", {"name": "System Information"})
    ET.SubElement(system, "variable", {"name": "RTI Server Address", "sysvar": "RTIServerAddress", "type": "string", "sample": "192.168.102.232"})
    ET.SubElement(system, "variable", {"name": "Variables Discovered", "sysvar": "VariablesDiscovered", "type": "integer", "sample": str(len(variables))})
    ET.SubElement(system, "variable", {"name": "Last Discovery Time", "sysvar": "LastDiscoveryTime", "type": "string", "sample": "2024-01-01 12:00:00"})
    ET.SubElement(system, "variable", {"name": "Matter Devices Connected", "sysvar": "MatterDevicesConnected", "type": "integer", "sample": "0"})

    discovered = ET.SubElement(root, "category", {"name": "Discovered Variables"})
    for variable in variables:
        variable_element(discovered, variable)

    matter_devices = sorted({variable.device for variable in variables if variable.device})
    if matter_devices:
        devices = ET.SubElement(root, "category", {"name": "Matter Devices"})
        for index, device in enumerate(matter_devices, start=1):
            ET.SubElement(devices, "variable", {"name": device, "sysvar": f"MatterDevice{index:03d}", "type": "string", "sample": "{}"})

    debug = ET.SubElement(root, "category", {"name": "Debug Information"})
    ET.SubElement(debug, "variable", {"name": "Last WebSocket Message", "sysvar": "LastWebSocketMessage", "type": "string", "sample": "Connection established"})
    ET.SubElement(debug, "variable", {"name": "Messages Received", "sysvar": "MessagesReceived", "type": "integer", "sample": "0"})
    ET.SubElement(debug, "variable", {"name": "Subscriptions Active", "sysvar": "SubscriptionsActive", "type": "integer", "sample": "0"})

    rough = ET.tostring(root, encoding="utf-8")
    pretty = minidom.parseString(rough).toprettyxml(indent="\t")
    return pretty.replace("<?xml version=\"1.0\" ?>", "<?xml version=\"1.0\" encoding=\"utf-8\" ?>", 1)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract tracked RTI system variables from an .apex file and generate Matterbridge driver artifacts."
    )
    parser.add_argument("apex_file", type=Path, help="Path to a real RTI .apex project/export file.")
    parser.add_argument("--mapping", type=Path, default=Path("rti_apex_variable_mapping.json"), help="Mapping JSON output path.")
    parser.add_argument("--system-variables", type=Path, help="Optional SystemVariables.xml output path.")
    parser.add_argument("--min-variables", type=int, default=1, help="Fail if fewer variables are extracted.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    variables = extract_apex_variables(args.apex_file)
    if len(variables) < args.min_variables:
        raise SystemExit(f"Found {len(variables)} variable(s), expected at least {args.min_variables}.")

    write_json(args.mapping, build_mapping(args.apex_file, variables))
    if args.system_variables:
        write_text(args.system_variables, build_system_variables_xml(variables))

    print(f"Extracted {len(variables)} variable(s)")
    print(f"Wrote mapping: {args.mapping}")
    if args.system_variables:
        print(f"Wrote system variables: {args.system_variables}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
