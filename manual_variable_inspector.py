#!/usr/bin/env python3
"""
Manual RTI Variable Inspector
Helps you capture variable names and IDs while using the diagnostics page
"""

import json
import time
from datetime import datetime

class RTIVariableInspector:
    """Tool to help manually inspect and catalog RTI variables"""
    
    def __init__(self):
        self.variables = {}
        self.current_session = {
            "start_time": datetime.now().isoformat(),
            "variables_found": 0
        }
    
    def add_variable(self, var_id, name, value=None, description=""):
        """Add a discovered variable to the catalog"""
        self.variables[var_id] = {
            "id": var_id,
            "name": name,
            "value": value,
            "description": description,
            "discovered_at": datetime.now().isoformat(),
            "homekit_type": self.guess_homekit_type(name, value)
        }
        self.current_session["variables_found"] += 1
        print(f"✓ Added Variable {var_id}: {name}")
        if value:
            print(f"  Value: {value}")
        print(f"  HomeKit Type: {self.variables[var_id]['homekit_type']}")
        print()
    
    def guess_homekit_type(self, name, value):
        """Guess the appropriate HomeKit accessory type based on name and value"""
        name_lower = name.lower()
        
        # Light-related
        if any(word in name_lower for word in ['light', 'lamp', 'bulb', 'fixture']):
            if value and isinstance(value, str) and '%' in str(value):
                return "lightbulb"  # Dimmer
            return "switch"  # On/off switch
        
        # Switch-related
        if any(word in name_lower for word in ['switch', 'outlet', 'plug', 'power']):
            return "switch"
        
        # Lock-related
        if any(word in name_lower for word in ['lock', 'door', 'gate']):
            return "lock"
        
        # Sensor-related
        if any(word in name_lower for word in ['sensor', 'motion', 'door', 'window', 'temp', 'temperature', 'humidity']):
            return "sensor"
        
        # Time-related
        if any(word in name_lower for word in ['time', 'clock', 'timer']):
            return "sensor"
        
        # Fan-related
        if any(word in name_lower for word in ['fan', 'vent', 'air']):
            return "fan"
        
        # Blinds/Shades
        if any(word in name_lower for word in ['blind', 'shade', 'curtain', 'drape']):
            return "window_covering"
        
        # Default to switch for unknown types
        return "switch"
    
    def display_catalog(self):
        """Display the current variable catalog"""
        print("\n" + "="*60)
        print("RTI VARIABLE CATALOG")
        print("="*60)
        print(f"Session started: {self.current_session['start_time']}")
        print(f"Variables found: {self.current_session['variables_found']}")
        print()
        
        if not self.variables:
            print("No variables discovered yet.")
            print("\nTo add variables:")
            print("1. Open the RTI diagnostics page in your browser")
            print("2. Check the checkboxes for different variables")
            print("3. Use the 'add' command to record what you see")
            return
        
        # Sort by ID
        sorted_vars = sorted(self.variables.items(), key=lambda x: x[0])
        
        for var_id, var_data in sorted_vars:
            print(f"ID {var_id:3d}: {var_data['name']}")
            if var_data['value']:
                print(f"       Value: {var_data['value']}")
            print(f"       HomeKit Type: {var_data['homekit_type']}")
            if var_data['description']:
                print(f"       Description: {var_data['description']}")
            print()
    
    def save_catalog(self, filename="rti_variables_catalog.json"):
        """Save the variable catalog to a JSON file"""
        catalog = {
            "session": self.current_session,
            "variables": self.variables,
            "exported_at": datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(catalog, f, indent=2)
        
        print(f"✓ Catalog saved to {filename}")
    
    def generate_homekit_config(self):
        """Generate a HomeKit configuration from the catalog"""
        config = {
            "rti_server": {
                "host": "192.168.102.232",
                "port": 80
            },
            "homekit": {
                "bridge_name": "RTI Bridge",
                "port": 51826,
                "setup_code": "123-45-678"
            },
            "variables": []
        }
        
        for var_id, var_data in sorted(self.variables.items(), key=lambda x: x[0]):
            config["variables"].append({
                "id": var_id,
                "name": var_data["name"],
                "type": var_data["homekit_type"],
                "homekit_type": var_data["homekit_type"],
                "description": var_data["description"] or f"RTI Variable {var_id}",
                "current_value": var_data["value"]
            })
        
        with open("rti_homekit_config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✓ HomeKit configuration generated: rti_homekit_config.json")

def main():
    """Interactive variable inspector"""
    inspector = RTIVariableInspector()
    
    print("RTI Variable Inspector")
    print("="*40)
    print("This tool helps you catalog RTI variables manually.")
    print("Open the diagnostics page and check checkboxes to discover variables.")
    print()
    print("Commands:")
    print("  add <id> <name> [value] [description] - Add a variable")
    print("  list - Show current catalog")
    print("  save - Save catalog to file")
    print("  config - Generate HomeKit configuration")
    print("  help - Show this help")
    print("  quit - Exit")
    print()
    
    while True:
        try:
            command = input("RTI Inspector> ").strip().split()
            
            if not command:
                continue
            
            cmd = command[0].lower()
            
            if cmd == "quit" or cmd == "exit":
                print("Goodbye!")
                break
            
            elif cmd == "add":
                if len(command) < 3:
                    print("Usage: add <id> <name> [value] [description]")
                    continue
                
                var_id = int(command[1])
                name = command[2]
                value = command[3] if len(command) > 3 else None
                description = " ".join(command[4:]) if len(command) > 4 else ""
                
                inspector.add_variable(var_id, name, value, description)
            
            elif cmd == "list":
                inspector.display_catalog()
            
            elif cmd == "save":
                inspector.save_catalog()
            
            elif cmd == "config":
                inspector.generate_homekit_config()
            
            elif cmd == "help":
                print("\nCommands:")
                print("  add <id> <name> [value] [description] - Add a variable")
                print("  list - Show current catalog")
                print("  save - Save catalog to file")
                print("  config - Generate HomeKit configuration")
                print("  help - Show this help")
                print("  quit - Exit")
                print()
            
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for available commands")
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()


