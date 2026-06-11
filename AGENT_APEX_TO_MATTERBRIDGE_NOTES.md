# Agent notes: Apex extraction to Matterbridge coprocessor mapping

This document explains how the current repo turns an RTI `.apex` programming file into data the Matterbridge coprocessor can use for RTI activity switches.

## Current state

The implemented pipeline extracts **RTI system variable IDs** from the `.apex` file automatically. It does **not** yet extract RTI macro IDs/names automatically because we have not had a real `.apex` archive available in this VM to verify the macro schema. Macro names are currently supplied explicitly in `rti_switch_selection.json`.

Do not fabricate macro IDs or switch mappings. If a real `.apex` file is available, inspect its internal XML/JSON members first and extend the importer with tests based on that real structure.

## Data flow

```text
project.apex
  -> apex_variable_importer.py
  -> rti_apex_variable_mapping.json
  -> rti_switch_config_generator.py + rti_switch_selection.json
  -> rti_switches.json
  -> rti_matterbridge_integration.py --switch-config rti_switches.json
  -> Matterbridge coprocessor switch implementation
```

## Variable ID extraction

`apex_variable_importer.py` opens the `.apex` as either a ZIP archive or a plain file:

- ZIP members with `.xml`, `.json`, `.txt`, or `.apex` suffixes are read.
- Plain `.apex` files are read directly.

Extraction is intentionally broad because the actual Apex export schema is not confirmed yet:

- XML path: `extract_variables_from_xml()`
  - Recursively walks XML elements.
  - Treats an element as a variable when its tag or attributes look like variable/sysvar/system variable fields.
  - Candidate id attributes include `id`, `variableid`, `sysvarid`, `systemvariableid`, and `sysvar`.
  - Tracks parent device-ish context when labels mention `device`, `keypad`, `light`, `switch`, `dimmer`, `thermostat`, or `sensor`.
- JSON path: `extract_variables_from_json()`
  - Recursively walks dictionaries/lists.
  - Treats records with `variableid`, `sysvarid`, `systemvariableid`, or variable/sysvar-looking keys as variable records.
- Text fallback: `extract_variables_from_text()`
  - Uses regexes for patterns like `variable id: 966`, `sysvar=951`, or `Variable 966`.

All candidates are merged by numeric variable id. The output item includes:

```json
{
  "id": 966,
  "name": "Current Time",
  "type": "string",
  "source": "Project.xml",
  "device": "Current Time Sensor",
  "contexts": ["Current Time Sensor"],
  "sysvar": "DiscoveredVar966"
}
```

The `sysvar` field is generated as `DiscoveredVar###` because `RTI_Driver/main.js` updates driver variables using that convention when RTI WebSocket `Sysvar` messages arrive.

## Macro ID/name handling

Macro extraction is **not implemented yet**. Today, `rti_switch_config_generator.py` expects macro names from a human- or tool-authored selection file:

```json
{
  "switches": [
    {
      "id": "activity-main",
      "name": "Main Activity",
      "on_macro": "Main Activity On",
      "off_macro": "Main Activity Off",
      "feedback_variable_id": 951,
      "on_values": ["true", "1", "on"],
      "off_values": ["false", "0", "off"]
    }
  ]
}
```

The generator validates only that `feedback_variable_id` exists in `rti_apex_variable_mapping.json`. It does not validate `on_macro` or `off_macro` against `.apex` content yet.

## How to add real macro extraction

When a real `.apex` file is available:

1. Inspect archive members with Python `zipfile` or unzip into a temp directory.
2. Search for macro/action/activity records and identify stable fields:
   - macro id
   - macro name
   - activity/device association
   - on/off semantic hints
3. Add a `TrackedMacro` dataclass to `apex_variable_importer.py`.
4. Add XML/JSON/text macro extractors parallel to the variable extractors.
5. Extend `build_mapping()` to include a `macros` list.
6. Update `rti_switch_config_generator.py` so selection templates include discovered macro candidates next to discovered feedback variables.
7. Add tests using a small real-structure fixture, not invented field names.

Expected future mapping shape:

```json
{
  "source_apex": "project.apex",
  "variables": [],
  "macros": [
    {
      "id": "macro-identifier-from-apex",
      "name": "Exact RTI macro name",
      "source": "Project.xml",
      "contexts": ["Activity name"]
    }
  ]
}
```

## Coprocessor runtime link

`rti_switches.json` is the handoff file for the Matterbridge coprocessor. Each switch contains:

- `id`: Matter device id used by command payloads.
- `name`: Matter switch display name.
- `on_macro`: RTI macro to execute for Matter `on` / `turn_on`.
- `off_macro`: RTI macro to execute for Matter `off` / `turn_off`.
- `feedback.variable_id`: RTI WebSocket sysvar id to subscribe for state.
- `feedback.sysvar`: generated driver sysvar name, e.g. `DiscoveredVar951`.
- `feedback.on_values` / `feedback.off_values`: string values converted to Matter boolean state.

`rti_matterbridge_integration.py` loads this with `--switch-config`:

- `subscribe_tracked_variables()` subscribes every feedback variable id.
- `handle_matter_device_command()` maps the Matter command to `on_macro` or `off_macro`.
- `handle_rti_message()` passes subscribed sysvar updates into `RtiSwitchPlugin.handle_feedback()`.
- When feedback resolves to a boolean state, the bridge emits `rti_switch_state_update`.

That emitted update is the state feedback the native Matterbridge plugin or coprocessor layer should apply to the exposed switch endpoint.

## Important constraints

- The RTI processor driver cannot parse `.apex` files at runtime.
- The RTI processor driver cannot create new driver sysvars dynamically; `SystemVariables.xml` must be generated before packaging.
- Matterbridge should run on the Mac/Pi coprocessor, not on the RTI processor.
- Macro execution is still a dispatch hook in this repo. Before claiming end-to-end control, wire `execute_rti_macro()` to the real RTI macro invocation path and test it against the processor.
