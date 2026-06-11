# RTI Matterbridge Integration

This integration connects your RTI system to Matter devices through Matterbridge, allowing you to control RTI macros via Matter-compatible switches and devices.

## 🏗️ Architecture Overview

```
RTI System → RTI Driver → Matterbridge → Matter Bridge → Matter Devices
     ↓           ↓           ↓           ↓           ↓
  Variables   WebSocket   HTTP API   Matter API   Switches/Lights
```

## 📋 What We've Built

### 1. **Enhanced RTI Driver** (`RTI_Driver/`)
- **WebSocket Connection**: Connects to RTI diagnostics WebSocket
- **Variable Discovery**: Automatically discovers RTI system variables
- **Matterbridge Integration**: Sends RTI data to Matterbridge
- **Macro Execution**: Maps Matter device commands to RTI macros

### 2. **Matterbridge Configuration** (`matterbridge.toml`)
- **API Gateway**: HTTP API for RTI driver communication
- **Matter Bridge**: Connects to your `luligu/matterbridge:latest` container
- **Message Routing**: Routes messages between RTI and Matter

### 3. **Docker Setup** (`docker-compose.yml`)
- **Matterbridge Container**: Runs the messaging bridge
- **Matter Bridge Container**: Runs your Matter bridge
- **Network Configuration**: Connects all services

### 4. **Python Integration Script** (`rti_matterbridge_integration.py`)
- **Bidirectional Communication**: Handles RTI ↔ Matterbridge communication
- **Variable Monitoring**: Monitors RTI variable changes
- **Macro Mapping**: Maps Matter commands to RTI macros

## 🚀 Quick Start

### Step 1: Start the Services
```bash
# Start Matterbridge and Matter bridge
docker-compose up -d

# Verify services are running
docker ps
```

Open the Luligu Matterbridge web frontend at `http://localhost:8283` on the Docker host. The RTI API bridge remains on `http://localhost:4242`.

On macOS Docker Desktop, do not start the Luligu Matterbridge container with `--network host`; Docker Desktop may show the container as healthy while publishing no browser-accessible ports. Recreate it with normal port publishing instead:

```bash
docker stop matterbridge
docker rm matterbridge
docker run --name matterbridge \
  -p 8283:8283 \
  -p 5540-5559:5540-5559/udp \
  -v ~/matterbridge-data:/root/.matterbridge \
  --restart unless-stopped \
  -d luligu/matterbridge:latest \
  matterbridge -docker
```

Then confirm `docker port matterbridge` includes `8283/tcp -> 0.0.0.0:8283` and open `http://localhost:8283`.

### Step 2: Configure RTI Driver
1. Import `RTI_Driver/` into RTI Integration Designer
2. Configure settings:
   - **RTI Server Address**: `192.168.102.232`
   - **RTI Server Port**: `1234`
   - **Enable Matterbridge**: `true`
   - **Matterbridge URL**: `http://localhost:4242`
3. Deploy to your RTI processor

### Step 3: Run Integration Script
```bash
# Install dependencies
pip install websockets requests

# Run the integration
python3 rti_matterbridge_integration.py
```

For activity switches with on/off macros and sysvar feedback, follow `RTI_SWITCH_PLUGIN_README.md` to generate `rti_switches.json`, then run the integration with `--switch-config rti_switches.json`.

## 🚀 RTI Boot Variables

**Important**: RTI automatically sends all WebSocket variables when it boots up. This means:

- ✅ **No manual discovery needed** - RTI sends everything automatically
- ✅ **Faster connection** - Variables arrive immediately on connection
- ✅ **Complete data** - You get all variables, not just a subset
- ✅ **Real-time updates** - Changes are pushed as they happen

### Testing Boot Variables
```bash
# Test script to see RTI boot variables
python3 test_rti_boot_variables.py
```

This will connect to RTI and show you all the variables it sends on boot.

## 🔧 Configuration

### RTI Driver Settings
```xml
<category name="Matterbridge Integration">
    <setting name="Enable Matterbridge" type="boolean" variable="MatterbridgeEnabled" default="true"/>
    <setting name="Matterbridge URL" type="string" variable="MatterbridgeURL" default="http://localhost:4242"/>
    <setting name="Matterbridge Token" type="string" variable="MatterbridgeToken" default=""/>
    <setting name="Matterbridge Channel" type="string" variable="MatterbridgeChannel" default="rti-matter"/>
</category>
```

### Matterbridge Configuration
```toml
[api.rti]
BindAddress="0.0.0.0:4242"
Buffer=10000
Timeout=60

[matter.matter]
Server="localhost:5540"
Number="+1234567890"
Password="your_matter_password"
```

Docker publishes the Matterbridge frontend on TCP port `8283` and the Matter commissioning/device range on UDP ports `5540-5559`.

## 📊 Discovered Variables

From your RTI system, we've discovered:
- **Variables 1-16**: System variables (currently null)
- **Variable 951**: Boolean variable (value: true)
- **Variable 966**: Time variable (value: "19:21")

## 🔄 How It Works

### 1. **RTI Variable Discovery**
- Driver connects to RTI WebSocket (`ws://192.168.102.232:1234/diagnosticswss`)
- **RTI automatically sends all variables on boot** - no manual discovery needed
- Monitors for variable changes in real-time
- Sends updates to Matterbridge

### 2. **Matter Device Control**
- Matter devices send commands through Matter bridge
- Matterbridge routes commands to RTI driver
- RTI driver maps commands to macros
- Macros execute on RTI system

### 3. **Bidirectional Communication**
- RTI variable changes → Matterbridge → Matter devices
- Matter device commands → Matterbridge → RTI macros

## 🎯 Macro Mapping Examples

### Light Control
```javascript
// Matter command: turn_on light_1
// Maps to RTI macro: "Light_1_On"

// Matter command: set_brightness light_1 (brightness: 75)
// Maps to RTI macro: "Light_1_Brightness_75"
```

### Switch Control
```javascript
// Matter command: turn_on switch_2
// Maps to RTI macro: "Switch_2_On"

// Matter command: turn_off switch_2
// Maps to RTI macro: "Switch_2_Off"
```

### Thermostat Control
```javascript
// Matter command: set_temperature thermostat_1 (temperature: 72)
// Maps to RTI macro: "Thermostat_1_SetTemp_72"
```

## 🛠️ Available Functions

### RTI Driver Functions
- **Start Matterbridge Integration**: Connect to Matterbridge
- **Stop Matterbridge Integration**: Disconnect from Matterbridge
- **Show Matter Devices**: Display connected Matter devices
- **Export Variable Mapping**: Export variable and device mappings

### Integration Script Functions
- **Variable Discovery**: Automatically discover RTI variables
- **Macro Mapping**: Map Matter commands to RTI macros
- **Status Monitoring**: Monitor integration status
- **Error Handling**: Handle connection issues

## 📁 File Structure

```
RTI Siri Project/
├── RTI_Driver/                    # RTI driver package
│   ├── DriverManifest.xml         # Driver manifest
│   ├── ConfigSettings.xml         # Driver configuration
│   ├── SystemVariables.xml        # System variables
│   ├── SystemFunctions.xml        # Driver functions
│   ├── main.js                    # Main driver code
│   └── README.md                  # Driver documentation
├── matterbridge.toml              # Matterbridge configuration
├── docker-compose.yml             # Docker services
├── rti_matterbridge_integration.py # Python integration script
└── RTI_MATTERBRIDGE_README.md     # This file
```

## 🔍 Troubleshooting

### Connection Issues
- **RTI WebSocket**: Check RTI server address and port
- **Matterbridge**: Verify Docker containers are running
- **Matter Bridge**: Check Matter bridge configuration

### Variable Discovery
- **No Variables Found**: Try different variable ID ranges
- **Timeout Errors**: Increase discovery timeout
- **Connection Drops**: Check RTI system logs

### Macro Execution
- **Macros Not Executing**: Verify macro names in RTI system
- **Command Mapping**: Check macro mapping configuration
- **Device Types**: Ensure Matter device types are supported

## 📈 Next Steps

1. **Customize Macro Mappings**: Update the mapping functions for your specific RTI macros
2. **Add More Device Types**: Extend support for additional Matter device types
3. **Error Handling**: Implement robust error handling and reconnection logic
4. **Monitoring**: Add logging and monitoring for production use
5. **Testing**: Test with your actual RTI macros and Matter devices

## 🎉 Benefits

- **Universal Control**: Control RTI macros through any Matter-compatible device
- **HomeKit Integration**: Matter devices work natively with HomeKit
- **Siri Control**: Use Siri to control RTI macros via Matter devices
- **Scalable**: Easy to add new devices and macros
- **Reliable**: Uses established protocols and standards

## 📞 Support

For issues or questions:
1. Check the debug output in RTI Integration Designer
2. Verify Docker containers are running
3. Review the integration script logs
4. Check Matter bridge configuration
5. Consult RTI and Matter documentation

This integration provides a powerful bridge between your RTI system and modern smart home standards, enabling seamless control through Matter-compatible devices and HomeKit!
