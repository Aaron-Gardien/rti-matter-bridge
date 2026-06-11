# RTI activity switch plugin workflow

This workflow creates Matter switch devices for RTI activities. Each switch has:

- one RTI macro to turn the activity on
- one RTI macro to turn the activity off
- one RTI system variable subscription for feedback state

The toolchain does not invent macro names or device mappings. It validates your selected switches against variables extracted from the real `.apex` programming file.

## 1. Import variables from the Apex file

```bash
python3 apex_variable_importer.py project.apex \
  --mapping rti_apex_variable_mapping.json \
  --system-variables RTI_Driver/SystemVariables.xml
```

## 2. Create a switch selection template

```bash
python3 rti_switch_config_generator.py \
  --apex-mapping rti_apex_variable_mapping.json \
  --write-template rti_switch_selection.json
```

Edit `rti_switch_selection.json` and add one object per activity switch:

```json
{
  "switches": [
    {
      "id": "activity-id-from-your-project",
      "name": "Activity name from your project",
      "on_macro": "Exact RTI macro name for on",
      "off_macro": "Exact RTI macro name for off",
      "feedback_variable_id": 1234,
      "on_values": ["true", "1", "on"],
      "off_values": ["false", "0", "off"]
    }
  ]
}
```

## 3. Generate runtime switch config

```bash
python3 rti_switch_config_generator.py \
  --apex-mapping rti_apex_variable_mapping.json \
  --switch-selection rti_switch_selection.json \
  --output rti_switches.json
```

## 4. Run the RTI to Matterbridge bridge with switch mapping

```bash
python3 rti_matterbridge_integration.py \
  --mapping rti_apex_variable_mapping.json \
  --switch-config rti_switches.json
```

The bridge subscribes to every feedback variable from `rti_switches.json`. When a Matter switch command arrives, it dispatches the configured RTI macro. When the RTI processor sends a subscribed sysvar update, it emits an `rti_switch_state_update` payload containing the switch id, switch name, and boolean on/off state.

## Runtime payloads

Matter switch command expected by the bridge:

```json
{
  "type": "matter_device_command",
  "data": {
    "device_id": "activity-id-from-your-project",
    "command": "turn_on"
  }
}
```

Switch feedback emitted after RTI sysvar changes:

```json
{
  "type": "rti_switch_state_update",
  "data": {
    "device_id": "activity-id-from-your-project",
    "device_type": "switch",
    "state": {"on": true}
  }
}
```
