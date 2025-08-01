#!/usr/bin/env python3
"""
Debug what the /onboard route actually returns
"""

import requests
import subprocess
import time
import sys

def start_server():
    """Start the Flask development server"""
    print("Starting Flask server...")
    server_process = subprocess.Popen([
        sys.executable, "-c", 
        """
import sys
import os
sys.path.append('.')
from app import app
app.run(debug=False, port=5004, host='127.0.0.1')
        """
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    print("Flask server started on port 5004")
    return server_process

def debug_onboard_route():
    """Debug the onboard route response"""
    base_url = "http://localhost:5004"
    
    try:
        response = requests.get(f"{base_url}/onboard", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"Content-Length: {len(response.text)}")
        
        print("\n--- Response Content (first 1000 chars) ---")
        print(response.text[:1000])
        
        print("\n--- Response Content (last 500 chars) ---")
        print(response.text[-500:])
        
        # Check if it's a redirect page
        if 'redirect' in response.text.lower() or 'login' in response.text.lower():
            print("\n⚠️  Response appears to be a redirect or login page")
        
        # Save full response to file for inspection
        with open('debug_onboard_response.html', 'w') as f:
            f.write(response.text)
        print("\n✓ Full response saved to debug_onboard_response.html")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to access /onboard route: {e}")

def main():
    server_process = None
    
    try:
        server_process = start_server()
        debug_onboard_route()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()
            print("Flask server stopped")

if __name__ == "__main__":
    main()
