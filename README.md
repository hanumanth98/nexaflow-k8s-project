# NexaFlow — Cloud-Native Task Management Platform

NexaFlow is a microservices-based task management application
built using Python, Docker, GitHub, and Kubernetes.

## Microservices

- Frontend: Port 8080
- Tasks API: Port 8081
- Notifications API: Port 8082

## Architecture

Browser → Frontend → Tasks API → Notifications API

## Technologies

- Python
- Docker
- Docker Networking
- Git and GitHub
- Kubernetes

## Features

- Create tasks
- View tasks
- Simulated task notifications
- HTTP communication between microservices

## Limitations

Tasks are stored in memory and are lost when the Tasks
service restarts. Notifications are simulated.
