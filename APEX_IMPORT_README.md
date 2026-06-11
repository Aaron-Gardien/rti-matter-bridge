# RTI Apex variable import workflow

Use `apex_variable_importer.py` before packaging the RTI driver to attach RTI system variables from a real `.apex` export to the Matterbridge driver.

## Why this is a pre-deploy tool

The RTI processor driver can update only sysvars that already exist in `RTI_Driver/SystemVariables.xml`. It cannot read an `.apex` file or create new driver variables at runtime. The importer runs on a development machine, extracts variable references, and generates deployable driver artifacts.

## Import an Apex project

```bash
python3 apex_variable_importer.py /path/to/project.apex \
  --mapping rti_apex_variable_mapping.json \
  --system-variables RTI_Driver/SystemVariables.xml
```

Outputs:

- `rti_apex_variable_mapping.json` lists each tracked RTI variable, its driver sysvar name (`DiscoveredVar###`), source member, and any device context found in the `.apex` file.
- `RTI_Driver/SystemVariables.xml` declares the tracked variables so `RTI_Driver/main.js` can call `SetVariable("DiscoveredVar###", value)` when the RTI WebSocket sends changes.

The importer does not fabricate devices or variables. If it cannot find at least one variable, it fails and leaves you with no generated mapping.

## Matterbridge on the RTI processor

Running the Node/Docker Matterbridge services directly on an RTI processor is not supported by this driver package. The RTI processor JavaScript runtime is suitable for the RTI WebSocket driver logic, but the Matterbridge server should run on another host that the processor can reach over HTTP.

The practical architecture is:

1. Run the RTI driver on the processor.
2. Pre-generate `SystemVariables.xml` from the `.apex` project.
3. Run Matterbridge on a separate host.
4. Point the driver or `rti_matterbridge_integration.py` at the Matterbridge API URL.
