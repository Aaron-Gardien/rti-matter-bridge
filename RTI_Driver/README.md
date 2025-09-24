# RTI HomeKit Bridge Driver

This RTI driver discovers and displays system variables from your RTI system, providing the foundation for HomeKit integration.

## What This Driver Does

1. **Connects to RTI System**: Uses WebSocket to connect to your RTI diagnostics interface
2. **Discovers Variables**: Scans for system variables and their current values
3. **Displays Results**: Shows variable names, IDs, types, and current values
4. **Exports Data**: Creates JSON and XML files for further use

## Files Included

- `DriverManifest.xml` - RTI driver manifest
- `ConfigSettings.xml` - Driver configuration settings
- `SystemVariables.xml` - System variable definitions
- `SystemFunctions.xml` - Available driver functions
- `main.js` - Main driver JavaScript code
- `instructions.rtf` - Driver instructions

## Installation

1. **Copy the RTI_Driver folder** to your RTI Integration Designer
2. **Import the driver** into your RTI project
3. **Configure the settings**:
   - RTI Server Address: `192.168.102.232`
   - RTI Server Port: `1234`
   - WebSocket Endpoint: `/diagnosticswss`
4. **Deploy the driver** to your RTI processor

## Usage

### Basic Operation

1. **Connect**: The driver automatically connects to your RTI system
2. **Discover Variables**: Use the "Discover Variables" function to scan for variables
3. **View Results**: Check the "Discovered Variables" category to see found variables
4. **Export Mapping**: Use "Export Variable Mapping" to get JSON data

### Configuration Options

- **Start/End Variable ID**: Range of variable IDs to scan
- **Discovery Timeout**: How long to wait for each variable response
- **Auto Discover**: Automatically discover variables on startup
- **Debug Trace**: Enable detailed logging

### Available Functions

#### Connection Control
- **Connect**: Manually connect to RTI system
- **Disconnect**: Disconnect from RTI system
- **Reconnect**: Reconnect to RTI system

#### Variable Discovery
- **Discover Variables**: Scan for system variables
- **Refresh All Variables**: Re-subscribe to all discovered variables
- **Clear Discovered Variables**: Clear the discovered variable list

#### Variable Control
- **Subscribe to Variable**: Subscribe to a specific variable ID
- **Unsubscribe from Variable**: Unsubscribe from a specific variable ID
- **Test Variable Range**: Test the configured variable range

#### HomeKit Integration
- **Start HomeKit Bridge**: Start the HomeKit bridge (requires Python script)
- **Stop HomeKit Bridge**: Stop the HomeKit bridge
- **Export Variable Mapping**: Export variable mapping for HomeKit integration

#### Debug Functions
- **Show Connection Status**: Display connection information
- **Show Discovered Variables**: List all discovered variables
- **Show WebSocket Log**: Display WebSocket message statistics

## Expected Results

The driver will discover variables like:
- **Variable 1-16**: System variables (may have null values)
- **Variable 951**: Boolean variable (true/false)
- **Variable 966**: Time variable (HH:MM format)

## Troubleshooting

### Connection Issues
- Verify RTI server address and port
- Check that WebSocket endpoint is correct
- Ensure RTI system is accessible

### No Variables Found
- Try different variable ID ranges
- Increase discovery timeout
- Check RTI system logs

### Debug Information
- Enable debug trace for detailed logging
- Use "Show Connection Status" to verify connection
- Check "Last WebSocket Message" for recent activity

## Next Steps

1. **Review Discovered Variables**: Identify which variables control which devices
2. **Map Device Functions**: Associate variable names with actual device functions
3. **Create HomeKit Integration**: Use the exported mapping with HomeKit bridge
4. **Test and Refine**: Test the integration and adjust as needed

## Integration with HomeKit

Once variables are discovered, you can:
1. Use the exported JSON mapping
2. Run the Python HomeKit bridge script
3. Map RTI variables to HomeKit accessories
4. Control RTI devices through Siri and Home app

## Support

For issues or questions:
1. Check the debug output
2. Verify RTI system connectivity
3. Review the variable discovery results
4. Consult RTI documentation for WebSocket API details


