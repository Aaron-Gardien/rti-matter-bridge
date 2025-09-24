#!/usr/bin/env python3
"""
Test RTI Boot Variables
Connects to RTI WebSocket and waits for boot variables
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RTIBootVariableTest:
    def __init__(self, host: str = "192.168.102.232", port: int = 1234):
        self.host = host
        self.port = port
        self.websocket = None
        self.variables = {}
        self.message_count = 0
        
    async def connect(self):
        """Connect to RTI WebSocket"""
        try:
            uri = f"ws://{self.host}:{self.port}/diagnosticswss"
            logger.info(f"Connecting to {uri}...")
            self.websocket = await websockets.connect(uri)
            logger.info("✅ Connected to RTI WebSocket")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Disconnected from RTI WebSocket")
    
    async def listen_for_boot_variables(self, timeout: int = 30):
        """Listen for RTI boot variables"""
        logger.info(f"🎧 Listening for RTI boot variables (timeout: {timeout}s)...")
        logger.info("RTI will automatically send all variables when it boots up")
        
        try:
            # Set a timeout for listening
            async with asyncio.timeout(timeout):
                async for message in self.websocket:
                    await self.handle_message(message)
                    
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Timeout reached after {timeout} seconds")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("🔌 WebSocket connection closed")
        except Exception as e:
            logger.error(f"❌ Error listening: {e}")
    
    async def handle_message(self, message: str):
        """Handle incoming WebSocket message"""
        self.message_count += 1
        
        try:
            data = json.loads(message)
            
            if data.get("messageType") == "Sysvar":
                var_id = data.get("sysvarid")
                var_value = data.get("sysvarval")
                
                # Store variable
                self.variables[var_id] = {
                    "id": var_id,
                    "value": var_value,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"📊 Variable {var_id}: {var_value}")
                
            elif data.get("messageType") == "echo":
                logger.debug(f"🔄 Echo: {data.get('message', '')}")
                
            else:
                logger.debug(f"📨 Message: {data}")
                
        except json.JSONDecodeError:
            logger.error(f"❌ Failed to parse message: {message}")
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
    
    def print_summary(self):
        """Print summary of received variables"""
        logger.info("\n" + "="*60)
        logger.info("📋 RTI BOOT VARIABLES SUMMARY")
        logger.info("="*60)
        logger.info(f"Total messages received: {self.message_count}")
        logger.info(f"Variables discovered: {len(self.variables)}")
        logger.info("")
        
        if self.variables:
            logger.info("📊 Variables:")
            for var_id, var_data in sorted(self.variables.items()):
                logger.info(f"  ID {var_id:3d}: {var_data['value']} (at {var_data['timestamp']})")
        else:
            logger.info("❌ No variables received")
        
        logger.info("="*60)
    
    async def run(self, timeout: int = 30):
        """Main test function"""
        logger.info("🚀 RTI Boot Variables Test")
        logger.info("="*50)
        
        # Connect to RTI
        if not await self.connect():
            return
        
        try:
            # Listen for boot variables
            await self.listen_for_boot_variables(timeout)
            
        finally:
            # Disconnect and print summary
            await self.disconnect()
            self.print_summary()

async def main():
    """Main function"""
    test = RTIBootVariableTest()
    await test.run(timeout=30)  # Listen for 30 seconds

if __name__ == "__main__":
    asyncio.run(main())
