#!/usr/bin/env python3
"""
RTI to HomeKit Bridge
Connects to RTI system via WebSocket and exposes devices as HomeKit accessories
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
import websockets
from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_SWITCH, CATEGORY_LIGHTBULB, CATEGORY_SENSOR
from pyhap.service import Service
from pyhap.characteristic import Characteristic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RTISystemVariable:
    """Represents a system variable from the RTI system"""
    
    def __init__(self, var_id: int, name: str, var_type: str = "string"):
        self.var_id = var_id
        self.name = name
        self.var_type = var_type
        self.value = None
        self.subscribed = False
    
    def to_subscribe_message(self) -> dict:
        """Generate subscription message for this variable"""
        return {
            "type": "Subscribe",
            "resource": "Sysvar",
            "value": {"id": self.var_id, "status": True}
        }
    
    def to_unsubscribe_message(self) -> dict:
        """Generate unsubscription message for this variable"""
        return {
            "type": "Subscribe",
            "resource": "Sysvar", 
            "value": {"id": self.var_id, "status": False}
        }

class RTIWebSocketClient:
    """Handles WebSocket communication with RTI system"""
    
    def __init__(self, host: str = "192.168.102.232", port: int = 80):
        self.host = host
        self.port = port
        self.websocket = None
        self.connected = False
        self.variables: Dict[int, RTISystemVariable] = {}
        self.message_handlers = []
    
    async def connect(self):
        """Connect to RTI WebSocket"""
        try:
            # Try different WebSocket endpoints
            endpoints = [
                f"ws://{self.host}/diagnostics",
                f"ws://{self.host}/ws",
                f"ws://{self.host}/socket.io/"
            ]
            
            for endpoint in endpoints:
                try:
                    logger.info(f"Attempting to connect to {endpoint}")
                    self.websocket = await websockets.connect(endpoint)
                    self.connected = True
                    logger.info(f"Connected to {endpoint}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to connect to {endpoint}: {e}")
                    continue
            
            if not self.connected:
                raise Exception("Could not connect to any WebSocket endpoint")
                
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from RTI WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from RTI WebSocket")
    
    async def send_message(self, message: dict):
        """Send a message to the RTI system"""
        if not self.connected or not self.websocket:
            raise Exception("Not connected to RTI system")
        
        message_str = json.dumps(message)
        await self.websocket.send(message_str)
        logger.debug(f"Sent: {message_str}")
    
    async def subscribe_to_variable(self, variable: RTISystemVariable):
        """Subscribe to a system variable"""
        message = variable.to_subscribe_message()
        await self.send_message(message)
        variable.subscribed = True
        self.variables[variable.var_id] = variable
        logger.info(f"Subscribed to variable {variable.var_id} ({variable.name})")
    
    async def unsubscribe_from_variable(self, variable: RTISystemVariable):
        """Unsubscribe from a system variable"""
        message = variable.to_unsubscribe_message()
        await self.send_message(message)
        variable.subscribed = False
        logger.info(f"Unsubscribed from variable {variable.var_id} ({variable.name})")
    
    async def listen_for_messages(self):
        """Listen for incoming messages from RTI system"""
        if not self.connected or not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Received non-JSON message: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error listening for messages: {e}")
    
    async def handle_message(self, data: dict):
        """Handle incoming messages from RTI system"""
        message_type = data.get("messageType")
        
        if message_type == "Sysvar":
            var_id = data.get("sysvarid")
            var_value = data.get("sysvarval")
            
            if var_id in self.variables:
                self.variables[var_id].value = var_value
                logger.info(f"Variable {var_id} ({self.variables[var_id].name}) = {var_value}")
                
                # Notify handlers
                for handler in self.message_handlers:
                    try:
                        handler(var_id, var_value, self.variables[var_id])
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
        
        elif message_type == "echo":
            logger.debug(f"Echo: {data.get('message')}")
        
        else:
            logger.debug(f"Unknown message type: {message_type}")

class RTISwitch(Accessory):
    """HomeKit accessory representing an RTI switch/button"""
    
    def __init__(self, rti_client: RTIWebSocketClient, variable: RTISystemVariable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rti_client = rti_client
        self.variable = variable
        self.switch_service = self.add_preload_service("Switch")
        self.switch_char = self.switch_service.get_characteristic("On")
        
        # Set up characteristic callbacks
        self.switch_char.setter_callback = self.set_switch_state
        self.switch_char.getter_callback = self.get_switch_state
        
        # Register for RTI updates
        self.rti_client.message_handlers.append(self.on_rti_update)
    
    def set_switch_state(self, value: bool):
        """Called when HomeKit wants to change the switch state"""
        logger.info(f"Setting {self.variable.name} to {value}")
        # Here you would send a command to the RTI system
        # This depends on how RTI handles commands vs subscriptions
        asyncio.create_task(self.send_rti_command(value))
    
    def get_switch_state(self) -> bool:
        """Called when HomeKit wants to read the switch state"""
        # Convert RTI value to boolean
        if self.variable.value is None:
            return False
        
        # Simple conversion - you might need to adjust this based on your RTI values
        return str(self.variable.value).lower() in ['true', '1', 'on', 'yes']
    
    async def send_rti_command(self, value: bool):
        """Send command to RTI system"""
        # This is where you'd implement the actual RTI command
        # The format depends on your RTI system's command protocol
        command = {
            "type": "Command",  # or whatever the command type is
            "resource": "Sysvar",
            "value": {"id": self.variable.var_id, "value": str(value).lower()}
        }
        await self.rti_client.send_message(command)
    
    def on_rti_update(self, var_id: int, value: Any, variable: RTISystemVariable):
        """Called when RTI variable value changes"""
        if var_id == self.variable.var_id:
            # Update HomeKit characteristic
            new_state = self.get_switch_state()
            self.switch_char.set_value(new_state, should_notify=True)

class RTISensor(Accessory):
    """HomeKit accessory representing an RTI sensor (like time display)"""
    
    def __init__(self, rti_client: RTIWebSocketClient, variable: RTISystemVariable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rti_client = rti_client
        self.variable = variable
        
        # Create a custom service for the sensor
        self.sensor_service = self.add_preload_service("TemperatureSensor")  # Using temp sensor as base
        self.temp_char = self.sensor_service.get_characteristic("CurrentTemperature")
        
        # Register for RTI updates
        self.rti_client.message_handlers.append(self.on_rti_update)
    
    def on_rti_update(self, var_id: int, value: Any, variable: RTISystemVariable):
        """Called when RTI variable value changes"""
        if var_id == self.variable.var_id:
            # For time display, we could convert to a numeric value
            # or create a custom characteristic for text display
            if ":" in str(value):  # Time format
                try:
                    # Convert HH:MM to decimal hours for temperature display
                    hours, minutes = str(value).split(":")
                    decimal_time = float(hours) + float(minutes) / 60.0
                    self.temp_char.set_value(decimal_time, should_notify=True)
                except:
                    pass

class RTIHomeKitBridge:
    """Main bridge class that connects RTI system to HomeKit"""
    
    def __init__(self, rti_host: str = "192.168.102.232"):
        self.rti_client = RTIWebSocketClient(rti_host)
        self.driver = None
        self.bridge = None
        self.accessories = []
    
    async def setup_rti_variables(self):
        """Set up RTI system variables to monitor"""
        # Add the variables we discovered
        variables = [
            RTISystemVariable(966, "Current Time", "time"),
            # Add more variables as you discover them
            # RTISystemVariable(1, "Light 1", "switch"),
            # RTISystemVariable(2, "Light 2", "switch"),
            # etc.
        ]
        
        for var in variables:
            await self.rti_client.subscribe_to_variable(var)
    
    async def setup_homekit_accessories(self):
        """Set up HomeKit accessories for RTI variables"""
        self.bridge = Bridge(self.driver, "RTI Bridge")
        
        # Create accessories for each variable
        for var in self.rti_client.variables.values():
            if var.var_type == "switch":
                accessory = RTISwitch(
                    self.rti_client, 
                    var,
                    display_name=var.name,
                    aid=var.var_id
                )
            elif var.var_type == "time":
                accessory = RTISensor(
                    self.rti_client,
                    var,
                    display_name=var.name,
                    aid=var.var_id
                )
            else:
                continue
            
            self.bridge.add_accessory(accessory)
            self.accessories.append(accessory)
    
    async def start(self):
        """Start the RTI-HomeKit bridge"""
        try:
            # Connect to RTI system
            await self.rti_client.connect()
            
            # Set up variables
            await self.setup_rti_variables()
            
            # Set up HomeKit
            self.driver = AccessoryDriver(port=51826)
            await self.setup_homekit_accessories()
            
            # Start HomeKit driver
            self.driver.add_accessory(accessory=self.bridge)
            
            # Start listening for RTI messages
            listen_task = asyncio.create_task(self.rti_client.listen_for_messages())
            
            # Start HomeKit driver
            await self.driver.start()
            
            logger.info("RTI-HomeKit bridge started successfully!")
            logger.info("HomeKit pairing code: Check the logs for the setup code")
            
            # Keep running
            await listen_task
            
        except Exception as e:
            logger.error(f"Failed to start bridge: {e}")
            raise
        finally:
            await self.rti_client.disconnect()

async def main():
    """Main entry point"""
    bridge = RTIHomeKitBridge()
    await bridge.start()

if __name__ == "__main__":
    asyncio.run(main())


