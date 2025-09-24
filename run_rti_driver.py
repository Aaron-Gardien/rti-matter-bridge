#!/usr/bin/env python3
"""
RTI Driver Runner
Simple script to run the RTI basic driver and discover variables
"""

import asyncio
import json
import time
from rti_basic_driver import RTIBasicDriver

async def main():
    """Run the RTI driver and discover variables"""
    print("RTI HomeKit Bridge Driver")
    print("=" * 50)
    
    # Create driver instance
    driver = RTIBasicDriver(host="192.168.102.232", port=1234)
    
    # Connect to RTI system
    print("Connecting to RTI system...")
    if not await driver.connect():
        print("Failed to connect to RTI system")
        return
    
    try:
        # Discover variables
        print("Discovering variables...")
        variables = await driver.discover_variables(1, 50)
        
        # Print results
        driver.print_variable_summary()
        
        # Save results
        driver.save_discovery_results()
        driver.save_system_variables_xml()
        
        print("\n" + "=" * 50)
        print("DISCOVERY COMPLETE")
        print("=" * 50)
        print(f"Variables discovered: {len(variables)}")
        print("Files created:")
        print("- rti_variables_discovery.json")
        print("- SystemVariables.xml")
        print("\nNext steps:")
        print("1. Review the discovered variables")
        print("2. Use the RTI Driver package in Integration Designer")
        print("3. Map variables to your actual devices")
        print("4. Set up HomeKit integration")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await driver.disconnect()

if __name__ == "__main__":
    asyncio.run(main())


