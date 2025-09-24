# RTI to HomeKit Bridge

This project provides tools to connect your RTI (Remote Technologies Inc.) home automation system to Apple HomeKit, allowing you to control RTI devices through Siri and the Home app.

## What We Discovered

From analyzing your RTI server at `192.168.102.232`, we found:

- **WebSocket Communication**: RTI uses WebSocket for real-time device control
- **System Variables**: Devices are controlled via system variables with numeric IDs
- **Subscription Pattern**: Use `{"type":"Subscribe","resource":"Sysvar","value":{"id":X,"status":true}}` to subscribe
- **Response Pattern**: Get `{"messageType":"Sysvar","sysvarid":X,"sysvarval":"value"}` responses
- **Known Variable**: ID 966 = Current Time (returns HH:MM format)

## Files Overview

### Core Scripts
- `rti_homekit_bridge.py` - Main HomeKit bridge that exposes RTI devices as HomeKit accessories
- `test_rti_connection.py` - Test WebSocket connection to RTI system
- `discover_variables.py` - Discover all available RTI system variables
- `rti_scraper.py` - Web scraping tools for diagnostics page analysis

### Configuration
- `rti_config.json` - Configuration file for RTI server and variable mappings
- `requirements_homekit.txt` - Python dependencies for HomeKit integration

## Quick Start

### 1. Install Dependencies
```bash
pip3 install -r requirements_homekit.txt
```

### 2. Test RTI Connection
```bash
python3 test_rti_connection.py
```

### 3. Discover Available Variables
```bash
python3 discover_variables.py
```

### 4. Run HomeKit Bridge
```bash
python3 rti_homekit_bridge.py
```

## Detailed Setup

### Step 1: Find the Correct WebSocket Endpoint

The RTI diagnostics page uses WebSocket, but we need to find the exact endpoint:

1. Open `http://192.168.102.232/diagnostics#/diagnostics/variables` in your browser
2. Open Developer Tools (F12)
3. Go to Network tab
4. Filter by "WebSocket" or "WS"
5. Check some checkboxes on the page
6. Look for the WebSocket connection URL in the Network tab

### Step 2: Discover Your RTI Variables

Run the discovery script to find all available system variables:

```bash
python3 discover_variables.py
```

This will:
- Test variable IDs 0-99
- Subscribe to each one briefly
- Record any responses
- Save results to JSON files

### Step 3: Map Variables to Devices

Edit `rti_config.json` to map discovered variables to your actual devices:

```json
{
  "variables": [
    {
      "id": 966,
      "name": "Current Time",
      "type": "time",
      "homekit_type": "sensor"
    },
    {
      "id": 1,
      "name": "Living Room Light",
      "type": "switch",
      "homekit_type": "switch"
    }
  ]
}
```

### Step 4: Run the HomeKit Bridge

```bash
python3 rti_homekit_bridge.py
```

This will:
- Connect to your RTI system via WebSocket
- Subscribe to configured variables
- Expose them as HomeKit accessories
- Start a HomeKit bridge on port 51826

### Step 5: Add to HomeKit

1. Open the Home app on your iPhone/iPad
2. Tap "Add Accessory"
3. Scan the QR code or enter the setup code
4. Follow the pairing process

## Understanding RTI Variables

Based on your data, RTI uses this pattern:

### Subscription Message
```json
{
  "type": "Subscribe",
  "resource": "Sysvar", 
  "value": {"id": 966, "status": true}
}
```

### Response Message
```json
{
  "messageType": "Sysvar",
  "sysvarid": 966,
  "sysvarval": "19:21"
}
```

### Echo Confirmation
```json
{
  "messageType": "echo",
  "message": "{\"type\":\"Subscribe\",\"resource\":\"Sysvar\",\"value\":{\"id\":966,\"status\":true}}"
}
```

## Variable Types

Different variable types can be mapped to different HomeKit accessories:

- **Switches/Lights**: Boolean values (true/false, 1/0, on/off)
- **Dimmers**: Numeric values (0-100 for percentage)
- **Sensors**: Any value (temperature, time, status)
- **Locks**: Boolean values (locked/unlocked)

## Troubleshooting

### WebSocket Connection Issues
- Check that the RTI server is accessible: `ping 192.168.102.232`
- Verify the correct WebSocket endpoint using browser dev tools
- Try different endpoints in the configuration

### No Variables Found
- Run the discovery script multiple times
- Check that the diagnostics page is accessible
- Try different variable ID ranges in the discovery script

### HomeKit Pairing Issues
- Check that port 51826 is not in use
- Try a different setup code in the configuration
- Restart the HomeKit bridge

## Next Steps

1. **Discover More Variables**: Use the discovery script to find all your RTI devices
2. **Map Device Functions**: Figure out which variables control which lights, switches, etc.
3. **Add Command Support**: Implement RTI command sending for device control
4. **Create Custom Accessories**: Add support for dimmers, sensors, and other device types
5. **Add Error Handling**: Improve reliability and reconnection logic

## Contributing

Feel free to extend this project with:
- Support for more RTI device types
- Better error handling and reconnection
- Configuration UI
- Logging and monitoring
- Docker containerization

## Notes

- The RTI system appears to use a subscription-based model rather than direct commands
- You may need to implement command sending separately from variable subscription
- Some variables might be read-only (sensors) while others are controllable (switches)
- The WebSocket endpoint might be different from what we tested - check browser dev tools


