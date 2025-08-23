#!/usr/bin/env python3
"""
Simple HTTP server for Arxos frontend
Serves files and handles CORS properly
"""

import http.server
import socketserver
import os
from http.server import SimpleHTTPRequestHandler

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Change to frontend directory
        super().__init__(*args, directory="frontend", **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

PORT = 3000

if __name__ == "__main__":
    print(f"🌐 Starting Arxos Frontend Server on http://localhost:{PORT}")
    print(f"📁 Serving from: {os.path.join(os.getcwd(), 'frontend')}")
    print(f"🔗 Open http://localhost:{PORT} in your browser")
    print(f"Press Ctrl+C to stop\n")
    
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Frontend server stopped")