
import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.error import URLError

# Temporary in-memory storage
tasks = []

# Notifications service URL
NOTIFICATIONS_URL = os.getenv(
    "NOTIFICATIONS_URL",
    "http://localhost:8082"
)


class TaskHandler(BaseHTTPRequestHandler):

    def send_json(self, status_code, data):
        response = json.dumps(data).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()

        self.wfile.write(response)

    def do_GET(self):

        if self.path == "/health":
            self.send_json(200, {
                "service": "tasks",
                "status": "healthy"
            })

        elif self.path == "/tasks":
            self.send_json(200, {
                "tasks": tasks
            })

        else:
            self.send_json(404, {
                "error": "Endpoint not found"
            })

    def do_POST(self):

        if self.path != "/tasks":
            self.send_json(404, {
                "error": "Endpoint not found"
            })
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)

            if not isinstance(data, dict):
                self.send_json(400, {
                    "error": "JSON object required"
                })
                return

            title = data.get("title")

            if not isinstance(title, str) or not title.strip():
                self.send_json(400, {
                    "error": "Task title is required"
                })
                return

            task = {
                "id": str(uuid.uuid4()),
                "title": title.strip(),
                "status": "pending"
            }

            tasks.append(task)

            notification = {
                "task_id": task["id"],
                "message": "New task created"
            }

            notification_status = "sent"

            try:
                request = Request(
                    NOTIFICATIONS_URL + "/notify",
                    data=json.dumps(notification).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )

                with urlopen(request, timeout=5) as response:
                    response.read()

            except (URLError, TimeoutError) as error:
                notification_status = "failed"
                print("Notification error:", error, flush=True)

            self.send_json(201, {
                "task": task,
                "notification_status": notification_status
            })

        except (ValueError, UnicodeDecodeError):
            self.send_json(400, {
                "error": "Invalid JSON request"
            })


if __name__ == "__main__":

    server = HTTPServer(
        ("0.0.0.0", 8081),
        TaskHandler
    )

    print("Tasks API running on port 8081", flush=True)

    server.serve_forever()
