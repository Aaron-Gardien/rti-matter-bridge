#!/usr/bin/env python3
"""
RTI WebSocket Discovery and Testing Tool
Tests WebSocket connections without the timeout parameter issue
"""

import asyncio
import websockets
import json
import socket
from datetime import datetime
import requests

class RTIWebSocketTester:
    """Test WebSocket connections to RTI server"""
    
    def __init__(self, host="192.168.102.232"):
        self.host = host
        self.results = {
            "host": host,
            "test_time": datetime.now().isoformat(),
            "working_websockets": [],
            "failed_websockets": [],
            "http_responses": []
        }
        
        # WebSocket endpoints to test based on known RTI patterns
        self.websocket_endpoints = [
            (80, "/diagnosticswss"),  # From RTI driver documentation
            (80, "/diagnostics"),
            (80, "/ws"), 
            (80, "/websocket"),
            (1234, "/diagnosticswss"),
            (1234, "/ws"),
            (1234, "/websocket"),
            (5000, "/ws"),
            (5000, "/websocket")
        ]
    
    async def test_websocket_connection(self, port, endpoint):
        """Test a single WebSocket connection"""
        uri = f"ws://{self.host}:{port}{endpoint}"
        
        try:
            # Use a simpler connection approach
            websocket = await websockets.connect(uri)
            
            # Try to send a test message
            test_message = json.dumps({
                "type": "test",
                "timestamp": datetime.now().isoformat()
            })
            
            await websocket.send(test_message)
            
            # Try to receive a response (with short timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                result = {
                    "uri": uri,
                    "status": "connected_with_response",
                    "response": response[:200] + "..." if len(response) > 200 else response,
                    "success": True
                }
            except asyncio.TimeoutError:
                result = {
                    "uri": uri, 
                    "status": "connected_no_response",
                    "success": True
                }
            
            await websocket.close()
            return result
            
        except Exception as e:
            return {
                "uri": uri,
                "error": str(e),
                "success": False
            }
    
    def test_http_response_details(self, port, endpoint):
        """Get detailed HTTP response information"""
        try:
            url = f"http://{self.host}:{port}{endpoint}"
            response = requests.get(url, timeout=10)
            
            return {
                "url": url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_type": response.headers.get('content-type', ''),
                "content_length": len(response.text),
                "content_preview": response.text[:500] + "..." if len(response.text) > 500 else response.text,
                "success": True
            }
            
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "success": False
            }
    
    async def run_websocket_tests(self):
        """Run all WebSocket tests"""
        print("=== TESTING WEBSOCKET CONNECTIONS ===")
        
        for port, endpoint in self.websocket_endpoints:
            print(f"\nTesting ws://{self.host}:{port}{endpoint}...")
            
            result = await self.test_websocket_connection(port, endpoint)
            
            if result["success"]:
                print(f"✓ Connected: {result['status']}")
                if 'response' in result:
                    print(f"  Response: {result['response']}")
                self.results["working_websockets"].append(result)
            else:
                print(f"✗ Failed: {result['error']}")
                self.results["failed_websockets"].append(result)
            
            await asyncio.sleep(0.5)  # Small delay between tests
    
    def run_http_analysis(self):
        """Analyze HTTP responses in detail"""
        print("\n=== ANALYZING HTTP RESPONSES ===")
        
        # Test the known working endpoints
        endpoints_to_analyze = [
            (80, "/diagnostics"),
            (5000, "/"),
            (5000, "/diagnostics")
        ]
        
        for port, endpoint in endpoints_to_analyze:
            print(f"\nAnalyzing http://{self.host}:{port}{endpoint}...")
            
            result = self.test_http_response_details(port, endpoint)
            
            if result["success"]:
                print(f"✓ Status: {result['status_code']}")
                print(f"  Content-Type: {result['content_type']}")
                print(f"  Content-Length: {result['content_length']}")
                
                # Look for WebSocket references in the HTML
                content = result["content_preview"].lower()
                if "websocket" in content or "ws://" in content or "wss://" in content:
                    print("  🔍 Contains WebSocket references!")
                
                if "vue" in content or "vuejs" in content:
                    print("  🔍 Contains Vue.js references!")
                
                if "socket.io" in content:
                    print("  🔍 Contains Socket.IO references!")
                    
                self.results["http_responses"].append(result)
            else:
                print(f"✗ Failed: {result['error']}")
    
    def generate_summary(self):
        """Generate a summary of findings"""
        print(f"\n{'='*60}")
        print("RTI WEBSOCKET DISCOVERY SUMMARY")
        print(f"{'='*60}")
        
        print(f"Working WebSocket connections: {len(self.results['working_websockets'])}")
        for ws in self.results["working_websockets"]:
            print(f"  ✓ {ws['uri']} ({ws['status']})")
        
        print(f"\nFailed WebSocket connections: {len(self.results['failed_websockets'])}")
        
        print(f"\nHTTP endpoints analyzed: {len(self.results['http_responses'])}")
        for http in self.results["http_responses"]:
            print(f"  • {http['url']} -> {http['status_code']}")
        
        print("\nRECOMMENDATIONS:")
        if self.results["working_websockets"]:
            print("  1. Use working WebSocket endpoints for real-time communication")
            print("  2. Test variable subscriptions on working endpoints")
        else:
            print("  1. Check browser dev tools on diagnostics page for WebSocket URL")
            print("  2. WebSocket might use different port or require authentication")
        
        print("  3. Examine HTML content for JavaScript WebSocket initialization")
        print("  4. Try manual WebSocket connection from browser console")
    
    def save_results(self, filename="rti_websocket_results.json"):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✓ Results saved to {filename}")

async def main():
    tester = RTIWebSocketTester()
    
    print("RTI WebSocket Discovery Tool")
    print("=" * 40)
    
    # Test WebSocket connections
    await tester.run_websocket_tests()
    
    # Analyze HTTP responses
    tester.run_http_analysis()
    
    # Generate summary
    tester.generate_summary()
    
    # Save results
    tester.save_results()

if __name__ == "__main__":
    asyncio.run(main())

