#!/usr/bin/env python3
"""
RTI Basic Driver
A simple RTI driver that discovers and displays system variables with their IDs
Based on RTI SDK documentation for SystemVariables.xml
"""

import asyncio
import json
import websockets
import logging
import time
from typing import Dict, List, Any
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RTIBasicDriver:
    """Basic RTI driver for discovering system variables"""
    
    def __init__(self, host: str = "192.168.102.232", port: int = 1234):
        self.host = host
        self.port = port
        self.websocket = None
        self.connected = False
        self.discovered_variables = {}
        self.variable_categories = {}
        
    async def connect(self):
        """Connect to RTI WebSocket"""
        endpoint = f"ws://{self.host}:{self.port}/diagnosticswss"
        try:
            self.websocket = await websockets.connect(endpoint)
            self.connected = True
            logger.info(f"Connected to RTI system at {endpoint}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RTI system: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from RTI system")
    
    async def subscribe_to_variable(self, var_id: int) -> bool:
        """Subscribe to a system variable"""
        if not self.connected:
            return False
        
        message = {
            "type": "Subscribe",
            "resource": "Sysvar",
            "value": {"id": var_id, "status": True}
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Subscribed to variable {var_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to variable {var_id}: {e}")
            return False
    
    async def unsubscribe_from_variable(self, var_id: int) -> bool:
        """Unsubscribe from a system variable"""
        if not self.connected:
            return False
        
        message = {
            "type": "Subscribe",
            "resource": "Sysvar",
            "value": {"id": var_id, "status": False}
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Unsubscribed from variable {var_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unsubscribe from variable {var_id}: {e}")
            return False
    
    async def listen_for_variable_updates(self, timeout: float = 3.0) -> List[Dict]:
        """Listen for variable updates"""
        if not self.connected:
            return []
        
        updates = []
        start_time = time.time()
        
        try:
            while (time.time() - start_time) < timeout:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    if data.get("messageType") == "Sysvar":
                        var_id = data.get("sysvarid")
                        var_value = data.get("sysvarval")
                        
                        update = {
                            "id": var_id,
                            "value": var_value,
                            "timestamp": time.time()
                        }
                        updates.append(update)
                        
                        # Store in discovered variables
                        self.discovered_variables[var_id] = {
                            "id": var_id,
                            "value": var_value,
                            "name": f"Variable {var_id}",
                            "type": self.guess_variable_type(var_value),
                            "timestamp": time.time()
                        }
                        
                        logger.info(f"Variable {var_id}: {var_value}")
                    
                except asyncio.TimeoutError:
                    continue
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    break
        
        except Exception as e:
            logger.error(f"Error listening for updates: {e}")
        
        return updates
    
    def guess_variable_type(self, value: Any) -> str:
        """Guess the variable type based on value"""
        if value is None:
            return "string"
        
        value_str = str(value).lower()
        
        if value_str in ["true", "false", "1", "0", "on", "off"]:
            return "boolean"
        elif value_str.isdigit():
            return "integer"
        elif ":" in value_str and len(value_str) == 5:  # Time format HH:MM
            return "string"
        elif "%" in value_str:
            return "integer"  # Percentage
        else:
            return "string"
    
    async def discover_variables(self, start_id: int = 1, end_id: int = 100) -> Dict[int, Dict]:
        """Discover variables in a range"""
        logger.info(f"Discovering variables {start_id} to {end_id}")
        
        for var_id in range(start_id, end_id + 1):
            logger.info(f"Testing variable {var_id}...")
            
            # Subscribe to variable
            if await self.subscribe_to_variable(var_id):
                # Listen for updates
                updates = await self.listen_for_variable_updates(timeout=2.0)
                
                # Unsubscribe
                await self.unsubscribe_from_variable(var_id)
                
                # Small delay between tests
                await asyncio.sleep(0.5)
        
        return self.discovered_variables
    
    def create_system_variables_xml(self) -> str:
        """Create SystemVariables.xml content"""
        root = Element("variables")
        
        # Create categories based on variable types
        categories = {
            "System Variables": [],
            "Boolean Variables": [],
            "Integer Variables": [],
            "String Variables": []
        }
        
        # Categorize variables
        for var_id, var_data in self.discovered_variables.items():
            var_type = var_data["type"]
            
            if var_type == "boolean":
                categories["Boolean Variables"].append(var_data)
            elif var_type == "integer":
                categories["Integer Variables"].append(var_data)
            else:
                categories["String Variables"].append(var_data)
            
            categories["System Variables"].append(var_data)
        
        # Create XML structure
        for category_name, variables in categories.items():
            if not variables:
                continue
                
            category = SubElement(root, "category")
            category.set("name", category_name)
            
            for var_data in variables:
                variable = SubElement(category, "variable")
                variable.set("name", var_data["name"])
                variable.set("sysvar", f"sysvar_{var_data['id']}")
                variable.set("type", var_data["type"])
                
                if var_data["value"] is not None:
                    variable.set("sample", str(var_data["value"]))
                
                # Add format based on type
                if var_data["type"] == "boolean":
                    variable.set("format", "B:Off:On")
                elif var_data["type"] == "integer":
                    variable.set("min", "0")
                    variable.set("max", "100")
        
        # Pretty print XML
        rough_string = tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def save_system_variables_xml(self, filename: str = "SystemVariables.xml"):
        """Save SystemVariables.xml file"""
        xml_content = self.create_system_variables_xml()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        logger.info(f"SystemVariables.xml saved to {filename}")
        return xml_content
    
    def print_variable_summary(self):
        """Print a summary of discovered variables"""
        logger.info("\n" + "="*60)
        logger.info("RTI SYSTEM VARIABLES DISCOVERED")
        logger.info("="*60)
        
        if not self.discovered_variables:
            logger.info("No variables discovered")
            return
        
        # Sort by ID
        sorted_vars = sorted(self.discovered_variables.items(), key=lambda x: x[0])
        
        for var_id, var_data in sorted_vars:
            logger.info(f"ID {var_id:3d}: {var_data['name']}")
            logger.info(f"      Type: {var_data['type']}")
            logger.info(f"      Value: {var_data['value']}")
            logger.info(f"      SysVar: sysvar_{var_id}")
            logger.info()
        
        logger.info(f"Total variables discovered: {len(self.discovered_variables)}")
    
    def save_discovery_results(self, filename: str = "rti_variables_discovery.json"):
        """Save discovery results to JSON"""
        results = {
            "timestamp": time.time(),
            "host": self.host,
            "port": self.port,
            "variables": self.discovered_variables,
            "summary": {
                "total_variables": len(self.discovered_variables),
                "variable_types": {}
            }
        }
        
        # Count variable types
        for var_data in self.discovered_variables.values():
            var_type = var_data["type"]
            results["summary"]["variable_types"][var_type] = results["summary"]["variable_types"].get(var_type, 0) + 1
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Discovery results saved to {filename}")
        return results

async def main():
    """Main driver function"""
    driver = RTIBasicDriver()
    
    logger.info("RTI Basic Driver - Variable Discovery")
    logger.info("="*50)
    
    # Connect to RTI system
    if not await driver.connect():
        logger.error("Failed to connect to RTI system")
        return
    
    try:
        # Discover variables
        logger.info("Starting variable discovery...")
        variables = await driver.discover_variables(1, 100)
        
        # Print summary
        driver.print_variable_summary()
        
        # Save results
        driver.save_discovery_results()
        driver.save_system_variables_xml()
        
        logger.info("\n=== FILES CREATED ===")
        logger.info("- rti_variables_discovery.json - Raw discovery data")
        logger.info("- SystemVariables.xml - RTI driver configuration")
        
        logger.info("\n=== NEXT STEPS ===")
        logger.info("1. Review the discovered variables")
        logger.info("2. Use the SystemVariables.xml in your RTI driver")
        logger.info("3. Map variable names to actual device functions")
        logger.info("4. Test the variables with your HomeKit integration")
        
    except Exception as e:
        logger.error(f"Driver error: {e}")
    finally:
        await driver.disconnect()

if __name__ == "__main__":
    asyncio.run(main())


