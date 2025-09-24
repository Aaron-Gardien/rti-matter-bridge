#!/usr/bin/env python3
"""
RTI Server Port Scanner and Discovery Tool
Systematically scans ports and endpoints to discover all available services
"""

import socket
import requests
import asyncio
import websockets
import json
import time
from datetime import datetime
from urllib.parse import urljoin
import concurrent.futures
import threading

class RTIPortScanner:
    """Comprehensive RTI server port and endpoint scanner"""
    
    def __init__(self, host="192.168.102.232"):
        self.host = host
        self.results = {
            "host": host,
            "scan_time": datetime.now().isoformat(),
            "open_ports": [],
            "http_endpoints": [],
            "websocket_endpoints": [],
            "failed_connections": []
        }
        
        # Common ports to scan
        self.ports_to_scan = [
            21,   # FTP
            22,   # SSH
            23,   # Telnet
            25,   # SMTP
            53,   # DNS
            80,   # HTTP
            110,  # POP3
            143,  # IMAP
            443,  # HTTPS
            993,  # IMAPS
            995,  # POP3S
            1234, # RTI specific
            1883, # MQTT
            3000, # Common dev server
            3001, # Common dev server
            5000, # Common dev server
            5001, # Common dev server
            8000, # Common web server
            8080, # Common web server
            8443, # HTTPS alternate
            8888, # Common web server
            9000, # Common web server
        ]
        
        # WebSocket endpoints to test
        self.websocket_endpoints = [
            "/diagnostics",
            "/diagnosticswss", 
            "/ws",
            "/websocket",
            "/socket.io/",
            "/api/ws",
            "/realtime",
            "/live",
            "/stream"
        ]
        
        # HTTP endpoints to test
        self.http_endpoints = [
            "/",
            "/diagnostics",
            "/api",
            "/status",
            "/info",
            "/health",
            "/admin",
            "/config",
            "/system"
        ]
    
    def scan_port(self, port, timeout=3):
        """Scan a single port to see if it's open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.host, port))
            sock.close()
            
            if result == 0:
                print(f"✓ Port {port} is OPEN")
                return True
            else:
                print(f"✗ Port {port} is closed")
                return False
                
        except Exception as e:
            print(f"✗ Port {port} error: {e}")
            return False
    
    def scan_all_ports(self):
        """Scan all ports in the list"""
        print(f"\n=== SCANNING PORTS ON {self.host} ===")
        
        # Use threading for faster scanning
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.scan_port, port): port for port in self.ports_to_scan}
            
            for future in concurrent.futures.as_completed(futures):
                port = futures[future]
                try:
                    is_open = future.result()
                    if is_open:
                        self.results["open_ports"].append({
                            "port": port,
                            "status": "open",
                            "service": self.guess_service(port)
                        })
                except Exception as e:
                    print(f"Error scanning port {port}: {e}")
        
        print(f"\nFound {len(self.results['open_ports'])} open ports")
    
    def guess_service(self, port):
        """Guess the service running on a port"""
        services = {
            21: "FTP",
            22: "SSH", 
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            110: "POP3",
            143: "IMAP", 
            443: "HTTPS",
            993: "IMAPS",
            995: "POP3S",
            1234: "RTI System",
            1883: "MQTT",
            3000: "Web Server",
            3001: "Web Server",
            5000: "Web Server",
            5001: "Web Server", 
            8000: "Web Server",
            8080: "HTTP Proxy",
            8443: "HTTPS",
            8888: "Web Server",
            9000: "Web Server"
        }
        return services.get(port, "Unknown")
    
    def test_http_endpoint(self, port, endpoint, timeout=5):
        """Test an HTTP endpoint"""
        try:
            url = f"http://{self.host}:{port}{endpoint}"
            response = requests.get(url, timeout=timeout)
            
            return {
                "url": url,
                "status_code": response.status_code,
                "content_type": response.headers.get('content-type', ''),
                "content_length": len(response.text),
                "response_preview": response.text[:200] + "..." if len(response.text) > 200 else response.text,
                "success": True
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "url": url,
                "error": str(e),
                "success": False
            }
    
    def test_all_http_endpoints(self):
        """Test HTTP endpoints on all open ports"""
        print(f"\n=== TESTING HTTP ENDPOINTS ===")
        
        for port_info in self.results["open_ports"]:
            port = port_info["port"]
            
            # Skip non-HTTP ports
            if port in [21, 22, 25, 53, 110, 143, 993, 995, 1883]:
                continue
                
            print(f"\nTesting HTTP endpoints on port {port}...")
            
            for endpoint in self.http_endpoints:
                result = self.test_http_endpoint(port, endpoint)
                
                if result["success"]:
                    print(f"✓ {result['url']} -> {result['status_code']} ({result['content_type']})")
                    self.results["http_endpoints"].append(result)
                else:
                    print(f"✗ {result['url']} -> {result['error']}")
                    self.results["failed_connections"].append(result)
                
                time.sleep(0.1)  # Small delay between requests
    
    async def test_websocket_endpoint(self, port, endpoint, timeout=5):
        """Test a WebSocket endpoint"""
        try:
            uri = f"ws://{self.host}:{port}{endpoint}"
            
            async with websockets.connect(uri, timeout=timeout) as websocket:
                # Try to send a ping or test message
                await websocket.send(json.dumps({"type": "ping", "timestamp": datetime.now().isoformat()}))
                
                # Wait for a response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    return {
                        "uri": uri,
                        "status": "connected",
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "success": True
                    }
                except asyncio.TimeoutError:
                    return {
                        "uri": uri,
                        "status": "connected_no_response",
                        "success": True
                    }
                    
        except Exception as e:
            return {
                "uri": uri,
                "error": str(e),
                "success": False
            }
    
    async def test_all_websocket_endpoints(self):
        """Test WebSocket endpoints on all open ports"""
        print(f"\n=== TESTING WEBSOCKET ENDPOINTS ===")
        
        for port_info in self.results["open_ports"]:
            port = port_info["port"]
            
            # Focus on likely web ports
            if port not in [80, 443, 1234, 3000, 3001, 5000, 5001, 8000, 8080, 8443, 8888, 9000]:
                continue
                
            print(f"\nTesting WebSocket endpoints on port {port}...")
            
            for endpoint in self.websocket_endpoints:
                result = await self.test_websocket_endpoint(port, endpoint)
                
                if result["success"]:
                    print(f"✓ {result['uri']} -> {result['status']}")
                    if 'response' in result:
                        print(f"  Response: {result['response']}")
                    self.results["websocket_endpoints"].append(result)
                else:
                    print(f"✗ {result['uri']} -> {result['error']}")
                    self.results["failed_connections"].append(result)
                
                await asyncio.sleep(0.1)  # Small delay between requests
    
    def generate_report(self):
        """Generate a comprehensive report"""
        print(f"\n{'='*60}")
        print("RTI SERVER DISCOVERY REPORT")
        print(f"{'='*60}")
        print(f"Host: {self.results['host']}")
        print(f"Scan Time: {self.results['scan_time']}")
        print()
        
        # Open Ports Summary
        print("OPEN PORTS:")
        if self.results["open_ports"]:
            for port_info in sorted(self.results["open_ports"], key=lambda x: x["port"]):
                print(f"  Port {port_info['port']:5d}: {port_info['service']}")
        else:
            print("  No open ports found")
        print()
        
        # HTTP Endpoints Summary
        print("WORKING HTTP ENDPOINTS:")
        if self.results["http_endpoints"]:
            for endpoint in self.results["http_endpoints"]:
                if endpoint["status_code"] == 200:
                    print(f"  ✓ {endpoint['url']} ({endpoint['content_type']})")
                else:
                    print(f"  ? {endpoint['url']} -> {endpoint['status_code']}")
        else:
            print("  No working HTTP endpoints found")
        print()
        
        # WebSocket Endpoints Summary  
        print("WORKING WEBSOCKET ENDPOINTS:")
        if self.results["websocket_endpoints"]:
            for endpoint in self.results["websocket_endpoints"]:
                print(f"  ✓ {endpoint['uri']} ({endpoint['status']})")
        else:
            print("  No working WebSocket endpoints found")
        print()
        
        # Recommendations
        print("RECOMMENDATIONS:")
        if self.results["websocket_endpoints"]:
            print("  1. Use browser dev tools to monitor WebSocket traffic on working endpoints")
            print("  2. Test variable subscriptions through the web interface")
        
        if any(ep["status_code"] == 200 for ep in self.results["http_endpoints"]):
            print("  3. Examine HTTP responses for API documentation or interfaces")
        
        print("  4. Use the working endpoints for RTI integration")
        print()
    
    def save_results(self, filename="rti_discovery_results.json"):
        """Save results to a JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"✓ Results saved to {filename}")
    
    async def run_full_scan(self):
        """Run the complete discovery scan"""
        print("RTI Server Discovery Tool")
        print("=" * 40)
        
        # Step 1: Port scan
        self.scan_all_ports()
        
        # Step 2: HTTP endpoints
        self.test_all_http_endpoints()
        
        # Step 3: WebSocket endpoints
        await self.test_all_websocket_endpoints()
        
        # Step 4: Generate report
        self.generate_report()
        
        # Step 5: Save results
        self.save_results()

async def main():
    scanner = RTIPortScanner()
    await scanner.run_full_scan()

if __name__ == "__main__":
    asyncio.run(main())

