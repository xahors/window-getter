"""
Lightweight REST & Web Dashboard Server for window-getter using Python standard http.server.
"""

import json
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from window_getter.core.detector import get_detector
from window_getter.core.rules import RuleGenerator


class WindowGetterHTTPHandler(BaseHTTPRequestHandler):
    server_version = "WindowGetterHTTP/1.0"

    def log_message(self, format, *args):
        # Suppress verbose console logs for clean CLI execution
        pass

    def _send_json(self, data: dict, status_code: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filepath: str, mime_type: str = "text/html"):
        if not os.path.exists(filepath):
            self.send_error(404, "File Not Found")
            return
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        detector = get_detector()

        if path == "/":
            static_dir = os.path.join(os.path.dirname(__file__), "static")
            index_path = os.path.join(static_dir, "index.html")
            self._send_file(index_path, "text/html; charset=utf-8")
            return

        elif path == "/api/status":
            active_win = detector.get_active_window()
            self._send_json({
                "status": "online",
                "backend": detector.backend_name,
                "has_active_window": active_win is not None,
                "total_windows": len(detector.get_windows())
            })
            return

        elif path == "/api/active":
            active = detector.get_active_window()
            if active:
                self._send_json({"success": True, "window": active.to_dict()})
            else:
                self._send_json({"success": False, "message": "No active window detected"}, 404)
            return

        elif path == "/api/windows":
            windows = detector.get_windows()
            data = [w.to_dict() for w in windows]
            self._send_json({"success": True, "count": len(data), "windows": data})
            return

        elif path == "/api/workspaces":
            workspaces = detector.get_workspaces()
            data = [w.__dict__ for w in workspaces]
            self._send_json({"success": True, "workspaces": data})
            return

        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        detector = get_detector()

        # Read JSON body
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = {}
        if content_length > 0:
            try:
                raw_body = self.rfile.read(content_length).decode("utf-8")
                post_data = json.loads(raw_body)
            except Exception:
                post_data = {}

        query = str(post_data.get("query", "")).strip()

        if path == "/api/close":
            success, msg = detector.close_window(query)
            self._send_json({"success": success, "message": msg})
            return

        elif path == "/api/kill":
            pid = int(post_data.get("pid", 0)) if str(post_data.get("pid", "")).isdigit() else 0
            if pid <= 0 and query.isdigit():
                pid = int(query)
            success, msg = detector.kill_process(pid)
            self._send_json({"success": success, "message": msg})
            return

        elif path == "/api/relaunch":
            custom_cmd = str(post_data.get("command", "")).strip()
            success, msg = detector.relaunch_window(query, custom_command=custom_cmd)
            self._send_json({"success": success, "message": msg})
            return

        elif path == "/api/focus":
            success, msg = detector.focus_window(query)
            self._send_json({"success": success, "message": msg})
            return

        elif path == "/api/rule":
            win = detector.find_window(query)
            if not win:
                self._send_json({"success": False, "message": f"Window '{query}' not found"}, 404)
                return
            target = str(post_data.get("target", "hyprland"))
            snippet = RuleGenerator.generate_formatted_block(win, target)
            self._send_json({
                "success": True,
                "app_id": win.display_app_id,
                "title": win.display_title,
                "rule_snippet": snippet
            })
            return

        else:
            self.send_error(404, "Endpoint not found")


class WebServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.httpd: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self, block: bool = True):
        self.httpd = HTTPServer((self.host, self.port), WindowGetterHTTPHandler)
        print(f"🌐 [window-getter web] Dashboard running at http://{self.host}:{self.port}/")
        
        if block:
            try:
                self.httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down web server...")
                self.stop()
        else:
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
