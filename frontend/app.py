
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

TASKS_URL = os.getenv("TASKS_URL", "http://localhost:8081")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>NexaFlow - Task Management</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 650px;
            margin: 50px auto;
            padding: 20px;
            background: #f4f6f9;
        }
        h1 { color: #243b53; }
        input {
            padding: 12px;
            width: 65%;
        }
        button {
            padding: 12px;
            background: #2563eb;
            color: white;
            border: none;
            cursor: pointer;
        }
        li {
            background: white;
            padding: 12px;
            margin: 10px 0;
            border-radius: 6px;
        }
    </style>
</head>
<body>
    <h1>NexaFlow</h1>
    <p>Cloud-Native Task Management Platform</p>

    <input id="title" placeholder="Enter a task">
    <button onclick="createTask()">Create Task</button>

    <h2>Tasks</h2>
    <ul id="taskList"></ul>
    <p id="message"></p>

    <script>
        async function loadTasks() {
            try {
                const response = await fetch("/api/tasks");
                if (!response.ok) throw new Error("Unable to load tasks");

                const data = await response.json();
                const list = document.getElementById("taskList");
                list.replaceChildren();

                for (const task of data.tasks) {
                    const item = document.createElement("li");
                    item.textContent = task.title + " — " + task.status;
                    list.appendChild(item);
                }
            } catch (error) {
                document.getElementById("message").textContent =
                    error.message;
            }
        }

        async function createTask() {
            const input = document.getElementById("title");
            const title = input.value.trim();

            if (!title) {
                alert("Please enter a task");
                return;
            }

            try {
                const response = await fetch("/api/tasks", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({title: title})
                });

                if (!response.ok) throw new Error("Task creation failed");

                const data = await response.json();

                document.getElementById("message").textContent =
                    "Task created. Notification: " +
                    data.notification_status;

                input.value = "";
                await loadTasks();
            } catch (error) {
                document.getElementById("message").textContent =
                    error.message;
            }
        }

        loadTasks();
    </script>
</body>
</html>
"""


class FrontendHandler(BaseHTTPRequestHandler):

    def send_data(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def proxy_tasks(self, method):
        try:
            data = None

            if method == "POST":
                length = int(self.headers.get("Content-Length", 0))
                data = self.rfile.read(length)

            request = Request(
                TASKS_URL + "/tasks",
                data=data,
                headers={"Content-Type": "application/json"},
                method=method
            )

            with urlopen(request, timeout=5) as response:
                body = response.read()
                self.send_data(
                    response.status,
                    body,
                    "application/json"
                )

        except HTTPError as error:
            self.send_data(
                error.code,
                error.read(),
                "application/json"
            )

        except (URLError, TimeoutError):
            self.send_data(
                502,
                json.dumps({
                    "error": "Tasks service unavailable"
                }).encode("utf-8"),
                "application/json"
            )

    def do_GET(self):
        if self.path == "/":
            self.send_data(
                200,
                HTML.encode("utf-8"),
                "text/html; charset=utf-8"
            )

        elif self.path == "/health":
            self.send_data(
                200,
                json.dumps({
                    "service": "frontend",
                    "status": "healthy"
                }).encode("utf-8"),
                "application/json"
            )

        elif self.path == "/api/tasks":
            self.proxy_tasks("GET")

        else:
            self.send_data(
                404,
                b'{"error":"Not found"}',
                "application/json"
            )

    def do_POST(self):
        if self.path == "/api/tasks":
            self.proxy_tasks("POST")
        else:
            self.send_data(
                404,
                b'{"error":"Not found"}',
                "application/json"
            )


if __name__ == "__main__":
    server = HTTPServer(
        ("0.0.0.0", 8080),
        FrontendHandler
    )

    print("NexaFlow Frontend running on port 8080", flush=True)
    server.serve_forever()
