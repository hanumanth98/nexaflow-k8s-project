import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class NotificationHandler(BaseHTTPRequestHandler):

    # Send JSON responses to clients
    def send_json(self, status_code, data):
        response = json.dumps(data).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()

        self.wfile.write(response)

    # Handle GET requests
    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {
                "service": "notifications",
                "status": "healthy"
            })
        else:
            self.send_json(404, {
                "error": "Endpoint not found"
            })

    # Handle POST requests
    def do_POST(self):
        if self.path != "/notify":
            self.send_json(404, {
                "error": "Endpoint not found"
            })
            return

        try:
            content_length = int(
                self.headers.get("Content-Length", 0)
            )

            request_body = self.rfile.read(content_length)
            task_data = json.loads(request_body)

            print(
                "Notification received:",
                task_data,
                flush=True
            )

            self.send_json(200, {
                "status": "sent",
                "message": "Task notification processed",
                "task": task_data
            })

        except (ValueError, UnicodeDecodeError):
            self.send_json(400, {
                "error": "Invalid JSON request"
            })


if __name__ == "__main__":
    server = HTTPServer(
        ("0.0.0.0", 8082),
        NotificationHandler
    )

    print(
        "Notifications API running on port 8082",
        flush=True
    )

    server.serve_forever()