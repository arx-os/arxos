#!/usr/bin/env python3
"""
SVGX Web IDE - Browser-based playground for editing and previewing .svgx files.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from svgx_engine.parser import SVGXParser
from svgx_engine.compiler.svgx_to_svg import SVGXToSVGCompiler
from svgx_engine.tools.svgx_linter import SVGXLinter
import html

logger = logging.getLogger(__name__)


class SVGXWebIDE(BaseHTTPRequestHandler):
    """Simple web IDE for SVGX development."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/':
            self._serve_index()
        elif path == '/api/parse':
            self._handle_parse_request()
        elif path == '/api/compile':
            self._handle_compile_request()
        elif path == '/api/lint':
            self._handle_lint_request()
        elif path.startswith('/static/'):
            self._serve_static_file(path[8:])  # Remove /static/ prefix
        else:
            self._serve_404()

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/api/parse':
            self._handle_parse_request()
        elif path == '/api/compile':
            self._handle_compile_request()
        elif path == '/api/lint':
            self._handle_lint_request()
        else:
            self._serve_404()

    def _serve_index(self):
        """Serve the main IDE page."""
        html = self._get_index_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _get_index_html(self) -> str:
        """Get the main IDE HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SVGX Web IDE</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2em;
        }
        .content {
            display: flex;
            height: 600px;
        }
        .editor-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #ddd;
        }
        .preview-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .panel-header {
            background: #ecf0f1;
            padding: 10px 20px;
            border-bottom: 1px solid #ddd;
            font-weight: bold;
        }
        .editor {
            flex: 1;
            padding: 20px;
        }
        #svgx-editor {
            width: 100%;
            height: 100%;
            border: none;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            resize: none;
            outline: none;
        }
        .preview {
            flex: 1;
            padding: 20px;
            overflow: auto;
        }
        .controls {
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #ddd;
        }
        .btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        .btn:hover {
            background: #2980b9;
        }
        .btn.success {
            background: #27ae60;
        }
        .btn.warning {
            background: #f39c12;
        }
        .btn.danger {
            background: #e74c3c;
        }
        .status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 4px;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .status.warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .example-selector {
            margin-bottom: 10px;
        }
        .example-selector select {
            padding: 5px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SVGX Web IDE</h1>
            <p>Edit, preview, and validate SVGX files</p>
        </div>

        <div class="content">
            <div class="editor-panel">
                <div class="panel-header">
                    SVGX Editor
                </div>
                <div class="editor">
                    <div class="example-selector">
                        <label for="example-select">Load Example: </label>
                        <select id="example-select" onchange="loadExample()">
                            <option value="">Choose an example...</option>
                            <option value="basic_room">Basic Room</option>
                            <option value="electrical_system">Electrical System</option>
                            <option value="mechanical_system">Mechanical System</option>
                        </select>
                    </div>
                    <textarea id="svgx-editor" placeholder="Enter your SVGX code here..."></textarea>
                </div>
            </div>

            <div class="preview-panel">
                <div class="panel-header">
                    Preview
                </div>
                <div class="preview" id="preview">
                    <p style="text-align: center; color: #666; margin-top: 50px;">
                        Enter SVGX code to see the preview
                    </p>
                </div>
            </div>
        </div>

        <div class="controls">
            <button class="btn" onclick="parseSVGX()">Parse</button>
            <button class="btn" onclick="compileSVGX()">Compile to SVG</button>
            <button class="btn" onclick="lintSVGX()">Lint</button>
            <button class="btn success" onclick="exportSVG()">Export SVG</button>
            <button class="btn warning" onclick="exportJSON()">Export JSON</button>
            <button class="btn danger" onclick="clearEditor()">Clear</button>

            <div id="status"></div>
        </div>
    </div>

    <script>
        const examples = {
            basic_room: `<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="rm201" type="architecture.room" system="architecture">
    <arx:geometry x="0" y="0" width="3000mm" height="4000mm"/>
    <arx:tags>
      <tag>classroom</tag>
      <tag>first_floor</tag>
    </arx:tags>
  </arx:object>

  <path d="M0,0 L3000,0 L3000,4000 L0,4000 Z"
        style="stroke:black;fill:none;stroke-width:2"
        arx:layer="walls"
        arx:precision="1mm"/>

  <arx:object id="lf01" type="electrical.light_fixture" system="electrical">
    <arx:geometry x="1500" y="2000"/>
    <arx:behavior>
      <variables>
        <voltage unit="V">120</voltage>
        <power unit="W">20</power>
      </variables>
      <calculations>
        <current formula="power / voltage"/>
      </calculations>
    </arx:behavior>
  </arx:object>

  <circle cx="1500" cy="2000" r="50"
          style="fill:yellow;stroke:black;stroke-width:2"
          arx:layer="electrical"/>
</svg>`,

            electrical_system: `<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="panel1" type="electrical.panel" system="electrical">
    <arx:geometry x="100" y="100"/>
    <arx:behavior>
      <variables>
        <voltage unit="V">120</voltage>
        <capacity unit="A">100</capacity>
      </variables>
    </arx:behavior>
  </arx:object>

  <rect x="100" y="100" width="200" height="300"
        style="fill:gray;stroke:black;stroke-width:2"
        arx:layer="electrical"/>

  <arx:object id="outlet1" type="electrical.outlet" system="electrical">
    <arx:geometry x="400" y="200"/>
  </arx:object>

  <rect x="390" y="190" width="20" height="20"
        style="fill:white;stroke:black;stroke-width:1"
        arx:layer="electrical"/>

  <path d="M300,250 L390,200"
        style="stroke:black;stroke-width:2"
        arx:layer="electrical"/>
</svg>`,

            mechanical_system: `<svg xmlns="http://www.w3.org/2000/svg" xmlns:arx="http://arxos.io/svgx">
  <arx:object id="hvac1" type="mechanical.hvac" system="mechanical">
    <arx:geometry x="200" y="100"/>
    <arx:behavior>
      <variables>
        <temperature unit="C">22</temperature>
        <flow_rate unit="m3/s">0.5</flow_rate>
      </variables>
    </arx:behavior>
  </arx:object>

  <rect x="200" y="100" width="150" height="100"
        style="fill:lightblue;stroke:black;stroke-width:2"
        arx:layer="mechanical"/>

  <arx:object id="duct1" type="mechanical.duct" system="mechanical">
    <arx:geometry x="350" y="150"/>
  </arx:object>

  <rect x="350" y="140" width="200" height="20"
        style="fill:silver;stroke:black;stroke-width:1"
        arx:layer="mechanical"/>
</svg>`
        };

        function loadExample() {
            const select = document.getElementById('example-select');
            const example = examples[select.value];
            if (example) {
                document.getElementById('svgx-editor').value = example;
                parseSVGX();
            }
        }

        function parseSVGX() {
            const content = document.getElementById('svgx-editor').value;
            fetch('/api/parse', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content: content})
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success) {
                    updatePreview(data.svg);
                }
            })
            .catch(error => {
                showStatus('error', 'Failed to parse SVGX: ' + error);
            });
        }

        function compileSVGX() {
            const content = document.getElementById('svgx-editor').value;
            fetch('/api/compile', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content: content})
            })
            .then(response => response.json())
            .then(data => {
                showStatus(data.success ? 'success' : 'error', data.message);
                if (data.success) {
                    updatePreview(data.svg);
                }
            })
            .catch(error => {
                showStatus('error', 'Failed to compile SVGX: ' + error);
            });
        }

        function lintSVGX() {
            const content = document.getElementById('svgx-editor').value;
            fetch('/api/lint', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({content: content})
            })
            .then(response => response.json())
            .then(data => {
                const status = data.valid ? 'success' : 'warning';
                const message = data.valid ? 'No issues found!' : data.errors.join(', ');
                showStatus(status, message);
            })
            .catch(error => {
                showStatus('error', 'Failed to lint SVGX: ' + error);
            });
        }

        function updatePreview(svgContent) {
            const preview = document.getElementById('preview');
            preview.innerHTML = html.escape(svgContent);
        }

        function showStatus(type, message) {
            const status = document.getElementById('status');
            status.className = 'status ' + type;
            status.textContent = message;
        }

        function clearEditor() {
            document.getElementById('svgx-editor').value = '';
            document.getElementById('preview').innerHTML = '<p style="text-align: center; color: #666; margin-top: 50px;">Enter SVGX code to see the preview</p>';
            document.getElementById('status').textContent = '';
        }

        function exportSVG() {
            const content = document.getElementById('svgx-editor').value;
            if (content) {
                const blob = new Blob([content], {type: 'image/svg+xml'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'export.svgx';
                a.click();
                URL.revokeObjectURL(url);
            }
        }

        function exportJSON() {
            const content = document.getElementById('svgx-editor').value;
            if (content) {
                const blob = new Blob([content], {type: 'application/json'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'export.json';
                a.click();
                URL.revokeObjectURL(url);
            }
        }
    </script>
</body>
</html>"""

    def _handle_parse_request(self):
        """Handle SVGX parsing requests."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            content = data.get('content', '')
            parser = SVGXParser()

            try:
                elements = parser.parse(content)
                result = {
                    'success': True,
                    'message': f'Successfully parsed {len(elements)} elements',
                    'elements': [str(elem) for elem in elements]
                }
            except Exception as e:
                result = {
                    'success': False,
                    'message': f'Parse error: {str(e)}'
                }

        except Exception as e:
            result = {
                'success': False,
                'message': f'Request error: {str(e)}'
            }

        self._send_json_response(result)

    def _handle_compile_request(self):
        """Handle SVGX compilation requests."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            content = data.get('content', '')
            compiler = SVGXToSVGCompiler()

            try:
                svg_output = compiler.compile(content)
                result = {
                    'success': True,
                    'message': 'Successfully compiled to SVG',
                    'svg': svg_output
                }
            except Exception as e:
                result = {
                    'success': False,
                    'message': f'Compilation error: {str(e)}'
                }

        except Exception as e:
            result = {
                'success': False,
                'message': f'Request error: {str(e)}'
            }

        self._send_json_response(result)

    def _handle_lint_request(self):
        """Handle SVGX linting requests."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            content = data.get('content', '')
            linter = SVGXLinter()

            try:
                is_valid = linter.lint_content(content)
                result = {
                    'valid': is_valid,
                    'errors': linter.errors,
                    'warnings': linter.warnings,
                    'info': linter.info
                }
            except Exception as e:
                result = {
                    'valid': False,
                    'errors': [f'Linting error: {str(e)}'],
                    'warnings': [],
                    'info': []
                }

        except Exception as e:
            result = {
                'valid': False,
                'errors': [f'Request error: {str(e)}'],
                'warnings': [],
                'info': []
            }

        self._send_json_response(result)

    def _send_json_response(self, data: Dict[str, Any]):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _serve_static_file(self, filename: str):
        """Serve static files."""
        try:
            # For now, just return 404 for static files
            self._serve_404()
        except Exception as e:
            self._serve_404()

    def _serve_404(self):
        """Serve 404 error page."""
        self.send_response(404)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'404 Not Found')


def run_web_ide(port: int = 8080):
    """Run the SVGX Web IDE server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, SVGXWebIDE)
    print(f"SVGX Web IDE running at http://localhost:{port}")
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down SVGX Web IDE...")


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="SVGX Web IDE")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port to run on")

    args = parser.parse_args()
    run_web_ide(args.port)


if __name__ == "__main__":
    main()
