# NexaFlow — Cloud-Native Task Management Platform

A hands-on, three-service Python application built from scratch and deployed with Docker, GitHub Container Registry (GHCR), and Kubernetes. This repository demonstrates the complete development-to-deployment workflow, plus Kubernetes operational exercises.

> **Project status:** Application development, local Docker testing, Git/GitHub, private image publishing, Kubernetes deployment, and end-to-end testing have been completed. Self-healing, scaling, v2 rolling update/rollback, and failure-injection exercises are documented below as **practice steps**; mark them complete only after performing them.

## 1. Architecture

```text
Browser / curl
     |
     | NodePort 30080
     v
Frontend Service (nexaflow-frontend namespace)
     |
Frontend Pod (Python HTTP, port 8080)
     |
     | TASKS_URL=http://tasks.nexaflow-tasks.svc.cluster.local:8081
     v
Tasks Service (ClusterIP, nexaflow-tasks namespace)
     |
Tasks Pod (Python HTTP, port 8081; in-memory task list)
     |
     | NOTIFICATIONS_URL=http://notifications.nexaflow-notifications.svc.cluster.local:8082
     v
Notifications Service (ClusterIP, nexaflow-notifications namespace)
     |
Notifications Pod (Python HTTP, port 8082; simulated notification)
```

Each service has its own source code, Dockerfile, Deployment, and Service. Frontend is externally reachable through NodePort where the environment permits it; internal services use Kubernetes DNS and ClusterIP.

## 2. Technology stack

| Layer | Technology |
|---|---|
| Application | Python standard-library HTTP servers |
| Development | VS Code, Git Bash, Python |
| Containers | Docker Desktop, Dockerfiles, Docker CLI |
| Source control | Git and GitHub |
| Container registry | GitHub Container Registry (GHCR), private packages |
| Orchestration | Kubernetes multi-node cluster (KodeKloud playground) |
| Cluster access | `kubectl` in the playground |

## 3. Repository layout

```text
nexaflow-k8s-project/
├── .gitignore
├── README.md
├── frontend/
│   ├── app.py
│   └── Dockerfile
├── tasks/
│   ├── app.py
│   └── Dockerfile
├── notifications/
│   ├── app.py
│   └── Dockerfile
└── kubernetes/
    ├── namespaces.yaml
    ├── frontend.yaml
    ├── tasks.yaml
    └── notifications.yaml
```

## 4. End-to-end project workflow

### Phase 1 — Create the project and write application code

Create the folders in Git Bash:

```bash
mkdir -p nexaflow-k8s-project/{frontend,tasks,notifications,kubernetes}
cd nexaflow-k8s-project
code .
```

Write the application code manually in `frontend/app.py`, `tasks/app.py`, and `notifications/app.py`. The applications implement a frontend UI/API gateway, task creation/listing, and simulated notifications, respectively. Their inter-service URLs are controlled by `TASKS_URL` and `NOTIFICATIONS_URL`.

**Local development:** Start each application in a separate terminal, following the startup instructions in the source files. The service ports are Frontend `8080`, Tasks `8081`, and Notifications `8082`.

Verify the APIs using Git Bash (not PowerShell's `curl` alias):

```bash
curl -i http://localhost:8082/health
curl -i http://localhost:8081/health
curl -i http://localhost:8080/health
curl -i -X POST http://localhost:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"First NexaFlow task"}'
curl -i http://localhost:8080/api/tasks
```

Check the UI at `http://localhost:8080`. Stop all local Python servers with `Ctrl+C` before starting Docker containers on the same ports.

### Phase 2 — Write Dockerfiles

Create these three files yourself:

**`frontend/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]
```

**`tasks/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY app.py .
EXPOSE 8081
CMD ["python", "app.py"]
```

**`notifications/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY app.py .
EXPOSE 8082
CMD ["python", "app.py"]
```

`FROM` selects the base image, `WORKDIR` sets the working directory, `COPY` adds the application code, `EXPOSE` documents the listening port, and `CMD` starts the service.

### Phase 3 — Build and test containers locally

Start Docker Desktop and confirm the engine is running:

```bash
docker info
docker build -t nexaflow-notifications:v1 ./notifications
docker build -t nexaflow-tasks:v1 ./tasks
docker build -t nexaflow-frontend:v1 ./frontend
docker images
```

Create an isolated Docker network and run services in dependency order:

```bash
docker network create nexaflow-network

docker run -d --name nexaflow-notifications \
  --network nexaflow-network -p 8082:8082 \
  nexaflow-notifications:v1

docker run -d --name nexaflow-tasks \
  --network nexaflow-network -p 8081:8081 \
  -e NOTIFICATIONS_URL=http://nexaflow-notifications:8082 \
  nexaflow-tasks:v1

docker run -d --name nexaflow-frontend \
  --network nexaflow-network -p 8080:8080 \
  -e TASKS_URL=http://nexaflow-tasks:8081 \
  nexaflow-frontend:v1
```

Verify:

```bash
docker ps -a
docker logs nexaflow-notifications
docker logs nexaflow-tasks
docker logs nexaflow-frontend
curl -i http://localhost:8080/health
curl -i -X POST http://localhost:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Docker integration test"}'
curl -i http://localhost:8080/api/tasks
```

**Result:** Three independently built images and containers communicate over a user-defined Docker network.

### Phase 4 — Initialize Git and push to GitHub

Create `.gitignore`:

```gitignore
__pycache__/
*.pyc
.venv/
venv/
.env
.env.*
.vscode/
*.log
.DS_Store
Thumbs.db
```

Create a **public** GitHub repository named `nexaflow-k8s-project`, without initializing a README on GitHub. Then:

```bash
git init
git branch -M main
git add .
git commit -m 'Initial NexaFlow application and Dockerfiles'
git remote add origin https://github.com/hanumanth98/nexaflow-k8s-project.git
git push -u origin main
```

Do not commit access tokens, `.env` files, or Kubernetes registry Secrets.

### Phase 5 — Publish private images to GHCR

Use a GitHub Personal Access Token (classic) with package publishing permission (`write:packages`). Keep the token private and revoke any token accidentally exposed in screenshots or logs.

Authenticate from Git Bash without placing the token in shell history:

```bash
read -rsp 'GHCR publishing token: ' GHCR_TOKEN; echo
printf '%s' "$GHCR_TOKEN" | docker login ghcr.io \
  -u hanumanth98 --password-stdin
unset GHCR_TOKEN
```

Tag and push:

```bash
docker tag nexaflow-frontend:v1 ghcr.io/hanumanth98/nexaflow-frontend:v1
docker tag nexaflow-tasks:v1 ghcr.io/hanumanth98/nexaflow-tasks:v1
docker tag nexaflow-notifications:v1 ghcr.io/hanumanth98/nexaflow-notifications:v1

docker push ghcr.io/hanumanth98/nexaflow-frontend:v1
docker push ghcr.io/hanumanth98/nexaflow-tasks:v1
docker push ghcr.io/hanumanth98/nexaflow-notifications:v1
```

**Visibility:** GitHub source repository is public; all three GHCR image packages remain **private**.

### Phase 6 — Write Kubernetes manifests

Create the four files in `kubernetes/` manually. The complete reference manifests are in this repository:

- `kubernetes/namespaces.yaml`: `nexaflow-frontend`, `nexaflow-tasks`, `nexaflow-notifications` namespaces.
- `kubernetes/notifications.yaml`: Notifications Deployment and ClusterIP Service on port `8082`.
- `kubernetes/tasks.yaml`: Tasks Deployment and ClusterIP Service on port `8081`, with cross-namespace `NOTIFICATIONS_URL`.
- `kubernetes/frontend.yaml`: Frontend Deployment and NodePort Service (`8080:30080`), with cross-namespace `TASKS_URL`.

The Deployments use `ghcr-secret` in `imagePullSecrets`, one replica per service, CPU request `50m`, memory request `64Mi`, CPU limit `200m`, and memory limit `128Mi`.

Commit the manifests:

```bash
git add kubernetes/
git commit -m 'Add NexaFlow Kubernetes Deployments and Services'
git push origin main
```

### Phase 7 — Deploy to Kubernetes multi-node playground

The KodeKloud playground is temporary (approximately one hour per session). Prepare and commit all files **before** starting it. `kubectl` is available inside the playground; local installation is not required.

```bash
kubectl cluster-info
kubectl get nodes -o wide
git clone https://github.com/hanumanth98/nexaflow-k8s-project.git
cd nexaflow-k8s-project
kubectl apply --dry-run=client -f kubernetes/namespaces.yaml
kubectl apply -f kubernetes/namespaces.yaml
kubectl get namespaces
```

Create a separate **read-only** GHCR classic token with `read:packages`. Enter it securely in the playground and create the image-pull Secret in **each** namespace:

```bash
read -rsp 'GHCR read-only token: ' GHCR_TOKEN; echo
for ns in nexaflow-frontend nexaflow-tasks nexaflow-notifications; do
  kubectl create secret docker-registry ghcr-secret \
    --docker-server=ghcr.io \
    --docker-username=hanumanth98 \
    --docker-password="$GHCR_TOKEN" \
    --namespace="$ns"
done
unset GHCR_TOKEN
```

Do not print, screenshot, or commit Secret values. In real production systems, prefer short-lived credentials and managed registry identity integrations where available.

Apply manifests and wait for rollout:

```bash
kubectl apply --dry-run=client -f kubernetes/notifications.yaml
kubectl apply --dry-run=client -f kubernetes/tasks.yaml
kubectl apply --dry-run=client -f kubernetes/frontend.yaml

kubectl apply -f kubernetes/notifications.yaml
kubectl apply -f kubernetes/tasks.yaml
kubectl apply -f kubernetes/frontend.yaml

kubectl rollout status deployment/notifications -n nexaflow-notifications --timeout=120s
kubectl rollout status deployment/tasks -n nexaflow-tasks --timeout=120s
kubectl rollout status deployment/frontend -n nexaflow-frontend --timeout=120s

kubectl get pods -A -o wide
kubectl get deployments -A
kubectl get svc -A
```

**Observed result:** All three application Pods reached `1/1 Running`, Deployments reached `1/1 Ready`, and Frontend ran on `node01` while Tasks and Notifications ran on `node02` in the tested playground session. The node placement may differ on future sessions.

### Phase 8 — End-to-end Kubernetes verification

Use the **current** node IP from `kubectl get nodes -o wide`. The example IP below was observed in one playground session and will not necessarily be valid later.

```bash
NODE_IP=10.244.51.165  # replace with a current reachable worker-node IP
curl -i "http://${NODE_IP}:30080/health"
curl -i "http://${NODE_IP}:30080/"
curl -i -X POST "http://${NODE_IP}:30080/api/tasks" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Deploy NexaFlow on Kubernetes"}'
curl -i "http://${NODE_IP}:30080/api/tasks"

kubectl logs -n nexaflow-frontend deployment/frontend --tail=30
kubectl logs -n nexaflow-tasks deployment/tasks --tail=30
kubectl logs -n nexaflow-notifications deployment/notifications --tail=30

kubectl get endpoints -n nexaflow-frontend
kubectl get endpoints -n nexaflow-tasks
kubectl get endpoints -n nexaflow-notifications
```

If the sandbox blocks direct NodePort access, test from inside the cluster or use `kubectl port-forward -n nexaflow-frontend svc/frontend 8080:8080` from a terminal that can reach the forwarded port.

**Observed result:** The app was accessible and the end-to-end task/notification flow was tested successfully.

## 5. Kubernetes operational exercises — perform and record results

The following exercises are the remaining project work. They are **instructions**, not claims that the tests have already been completed.

### Exercise A — Self-healing

```bash
kubectl get pods -n nexaflow-frontend -o wide
kubectl delete pod -n nexaflow-frontend \
  $(kubectl get pods -n nexaflow-frontend -l app=frontend \
    -o jsonpath='{.items[0].metadata.name}')
kubectl get pods -n nexaflow-frontend -w
# Ctrl+C when the replacement Pod is running
kubectl get deployment frontend -n nexaflow-frontend
kubectl get events -n nexaflow-frontend --sort-by=.metadata.creationTimestamp
```

**Expected:** The ReplicaSet creates a replacement Pod. With one replica, temporary downtime is possible.

### Exercise B — Frontend scaling

```bash
kubectl scale deployment/frontend --replicas=3 -n nexaflow-frontend
kubectl rollout status deployment/frontend -n nexaflow-frontend --timeout=120s
kubectl get pods -n nexaflow-frontend -o wide
kubectl get endpoints -n nexaflow-frontend
kubectl scale deployment/frontend --replicas=1 -n nexaflow-frontend
kubectl rollout status deployment/frontend -n nexaflow-frontend --timeout=120s
```

**Expected:** Frontend reaches `3/3` and returns to `1/1`. The scheduler may place multiple Pods on one node. Do not scale Tasks without shared persistent storage: its in-memory task list is not replicated.

### Exercise C — Build and release Frontend v2

On the laptop, change the visible HTML heading in `frontend/app.py` from `NexaFlow` to `NexaFlow v2`. Preserve all API routes. Build and push:

```bash
docker build -t nexaflow-frontend:v2 ./frontend
docker tag nexaflow-frontend:v2 ghcr.io/hanumanth98/nexaflow-frontend:v2
docker push ghcr.io/hanumanth98/nexaflow-frontend:v2
```

Update `kubernetes/frontend.yaml` image to `ghcr.io/hanumanth98/nexaflow-frontend:v2`. For the rolling-update exercise, add under the Deployment's `spec` (not the Service):

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

Commit and push:

```bash
git add frontend/app.py kubernetes/frontend.yaml
git commit -m 'Release NexaFlow frontend v2'
git push origin main
```

In the playground, pull the updated Git commit and apply:

```bash
cd ~/nexaflow-k8s-project  # or the actual clone directory
git pull origin main
kubectl apply -f kubernetes/frontend.yaml
kubectl rollout status deployment/frontend -n nexaflow-frontend --timeout=180s
kubectl get deployment frontend -n nexaflow-frontend \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

Check that the new heading is served via NodePort. A `maxSurge: 1` rollout temporarily needs capacity for an additional Pod.

### Exercise D — Roll back

```bash
kubectl rollout history deployment/frontend -n nexaflow-frontend
kubectl rollout undo deployment/frontend -n nexaflow-frontend
kubectl rollout status deployment/frontend -n nexaflow-frontend --timeout=180s
kubectl get deployment frontend -n nexaflow-frontend \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

Verify that the image returned to `v1`. **Important:** `rollout undo` changes the cluster, not Git. If the rollback should remain in effect, update `kubernetes/frontend.yaml` back to `v1` and commit the change.

### Exercise E — Troubleshoot ImagePullBackOff

Deliberately use an invalid image tag:

```bash
kubectl set image deployment/frontend \
  frontend=ghcr.io/hanumanth98/nexaflow-frontend:invalid-tag \
  -n nexaflow-frontend
kubectl get pods -n nexaflow-frontend
kubectl describe pods -n nexaflow-frontend -l app=frontend
kubectl get events -n nexaflow-frontend --sort-by=.metadata.creationTimestamp
```

Restore the known-good image:

```bash
kubectl set image deployment/frontend \
  frontend=ghcr.io/hanumanth98/nexaflow-frontend:v1 \
  -n nexaflow-frontend
kubectl rollout status deployment/frontend -n nexaflow-frontend --timeout=180s
```

**Diagnosis:** Check tag spelling, GHCR permissions, image-pull Secret, registry access, and event messages.

### Exercise F — Troubleshoot Pending Pods

```bash
kubectl set resources deployment/frontend -n nexaflow-frontend \
  --requests=cpu=50m,memory=100Gi
kubectl get pods -n nexaflow-frontend
kubectl describe pods -n nexaflow-frontend -l app=frontend
kubectl describe nodes
```

Restore:

```bash
kubectl set resources deployment/frontend -n nexaflow-frontend \
  --requests=cpu=50m,memory=64Mi \
  --limits=cpu=200m,memory=128Mi
kubectl rollout status deployment/frontend -n nexaflow-frontend --timeout=180s
```

**Diagnosis:** Look for scheduler events such as `Insufficient memory`. A previous healthy replica may remain available during a failed rollout.

### Exercise G — Troubleshoot Service routing

```bash
kubectl get svc -n nexaflow-tasks
kubectl get pods -n nexaflow-tasks --show-labels
kubectl get endpoints -n nexaflow-tasks
kubectl describe svc tasks -n nexaflow-tasks
kubectl logs deployment/tasks -n nexaflow-tasks --tail=50
kubectl get deployment frontend -n nexaflow-frontend \
  -o jsonpath='{.spec.template.spec.containers[0].env}{"\n"}'
```

**Diagnosis:** Check Service selectors, Pod labels, endpoint addresses, port mappings, DNS name, and application logs.

## 6. Operational commands quick reference

| Task | Command |
|---|---|
| List nodes | `kubectl get nodes -o wide` |
| List all application Pods | `kubectl get pods -A -o wide` |
| List Deployments | `kubectl get deployments -A` |
| List Services | `kubectl get svc -A` |
| Inspect a Pod | `kubectl describe pod POD -n NAMESPACE` |
| View logs | `kubectl logs deployment/NAME -n NAMESPACE --tail=50` |
| Check rollout | `kubectl rollout status deployment/NAME -n NAMESPACE` |
| Roll back | `kubectl rollout undo deployment/NAME -n NAMESPACE` |
| View events | `kubectl get events -n NAMESPACE --sort-by=.metadata.creationTimestamp` |

## 7. Results and evidence checklist

Add **your own screenshots** or terminal outputs to a future `docs/screenshots/` folder (never include secrets):

- [x] Python services written and tested locally
- [x] Three Dockerfiles written and images built
- [x] Three containers running on a Docker network
- [x] Code pushed to GitHub
- [x] Three private images pushed to GHCR
- [x] Kubernetes namespaces, Deployments, and Services created
- [x] All three application Pods running on the multi-node cluster
- [x] End-to-end API testing completed
- [ ] Pod self-healing demonstrated
- [ ] Frontend scaled to three replicas and back
- [ ] Frontend v2 built, published, and deployed
- [ ] Rollback to v1 demonstrated
- [ ] Image pull failure diagnosed and recovered
- [ ] Unschedulable Pod diagnosed and recovered
- [ ] Service routing troubleshooting documented

## 8. Limitations and production improvements

This is a **hands-on learning deployment**, not a production-ready platform:

- **Persistence:** Tasks exist only in the Tasks process memory. Restarting the Pod loses them; multiple Tasks replicas would have inconsistent state. Add PostgreSQL or another shared data store.
- **Notifications:** Simulated, not real email/SMS delivery.
- **Availability:** One replica per service initially; no guarantee of zero downtime during restarts.
- **Health management:** Readiness and liveness probes are not yet configured.
- **Security:** Use least-privilege registry credentials; Kubernetes Secrets need appropriate RBAC and encryption-at-rest configuration. Prefer managed workload identity in production.
- **CI/CD:** Builds and releases are manual. Add GitHub Actions with tests, image scanning, immutable image tags/digests, and controlled deployments.
- **Operations:** Add metrics, dashboards, centralized logs, alerts, and an ingress with TLS.
- **Configuration:** Add environment-specific configuration management and resource sizing based on measurements.

## 9. Recreate the deployment after a playground reset

Because the KodeKloud playground expires, each fresh session requires:

1. Start the multi-node playground and verify the nodes.
2. Clone the GitHub repository.
3. Apply `kubernetes/namespaces.yaml`.
4. Create `ghcr-secret` separately in all three namespaces using a read-only GHCR token.
5. Apply Notifications, Tasks, and Frontend manifests.
6. Wait for rollouts and test through the current reachable NodePort address.

Never assume a previous session's Pods, Secrets, node IPs, or in-memory task records still exist.

## 10. Interview-ready project summary

> Built NexaFlow, a three-service Python task-management application, from scratch. Authored Dockerfiles, built and tested images locally using Docker networking, managed source code in GitHub, and published private images to GHCR. Created Kubernetes namespaces, Deployments, and Services manually, configured private registry image pulls with Kubernetes Secrets, deployed across a multi-node cluster, and verified cross-namespace service communication and end-to-end API requests. The repository also contains guided exercises for self-healing, scaling, rolling releases, rollback, and troubleshooting.

**Repository:** https://github.com/hanumanth98/nexaflow-k8s-project
