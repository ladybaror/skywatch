# 🛰️ SkyWatch – Cloud-Native Local K3d Infrastructure & GitOps Pipeline

An end-to-end local infrastructure and automation setup for the **SkyWatch** application, built on a local **k3d (K3s in Docker)** cluster. This project demonstrates a fully automated pipeline starting from local development up to GitOps-driven deployment.

---

## 📐 System Architecture

The infrastructure is provisioned locally inside a multi-node k3d cluster hosting a Control Plane node and 2 dedicated Agent nodes separating workloads.

```text
+----------------------------------------------------------------------------------+

| Local Machine (Docker Desktop / Docker Daemon)                                   |
|                                                                                  |
|  +----------------------------------------------------------------------------+  |
|  | k3d (Lightweight K3s Kubernetes Cluster)                                   |  |
|  |                                                                            |  |
|  | [Server Node: server:0] (Tainted: NoSchedule)                              |  |
|  |                                                                            |  |
|  | [Agent Node 0: workload=argocd]                                            |  |
|  |  └── 🔄 ArgoCD v2.11.2 (GitOps Controller)                                 |  |
|  |                                                                            |  |
|  | [Agent Node 1: workload=app]                                               |  |
|  |  ├── 🌐 SkyWatch Frontend (Pod)                                            |  |
|  |  ├── 🐰 RabbitMQ 3.13-management (StatefulSet/Pod)                         |  |
|  |  └── ⚙️  SkyWatch Worker (Pod)                                              |  |
|  +----------------------------------------------------------------------------+  |
+----------------------------------------------------------------------------------+
                                      ▲
                                      │ Auto-Sync / Deployment
                                      │
               +----------------------+----------------------+

               |                                             |
    +--------------------+                        +--------------------+

    | GitHub Repository  |                        | Docker Hub Registry|
    | (Helm Charts &     |                        | (dianabaror/)      |
    | Manifests)         |                        | (Docker Images)    |
    +--------------------+                        +--------------------+
```

---

## 🛠️ Tech Stack

* **Local Cluster:** k3d v5+ (K3s in Docker containers).
* **Container Orchestration:** K3s v1.29.5 (Lightweight Kubernetes).
* **CI/CD Pipeline:** GitHub Actions (Lint → Multi-Stage Docker Build & Push to Docker Hub → Automatic YAML Version Tag Bump).
* **Packaging & GitOps:** Helm 3 + ArgoCD v2.11.2 (Automated Sync, Pruning, Self-healing).
* **Messaging & Processing:** RabbitMQ 3.13 + Python Workers + Node.js Frontend.

---

## 📂 Directory Structure

```text
skywatch/
├── .github/
│   └── workflows/
│       └── ci-cd.yaml          # CI/CD Pipeline for Testing, Building, and Pushing to Docker Hub
├── app/
│   ├── frontend/               # Frontend Application with Dockerfile
│   └── worker/                 # Worker Processing Application with Dockerfile
├── helm/
│   └── skywatch/               # Application Helm Chart
│       ├── Chart.yaml
│       └── values.yaml         # Resource Constraints & Image Configurations
└── argocd/
    └── application.yaml        # ArgoCD Application Manifest
```

---

## ⚡ Deployment & Setup Guide

### Prerequisites
* Installed on local machine: `Docker Desktop`, `k3d`, `kubectl`, `helm`.
* Active account on **Docker Hub**.

---

### Step 1: Bootstrap the Local Cluster with k3d

Create the cluster with a dedicated server control plane, 2 agents, dedicated ports, taints, and labels:

```powershell
k3d cluster create skywatch `
  --agents 2 `
  --port "8080:30000@server:0" `
  --k3s-arg "--node-taint=node-role.kubernetes.io/control-plane:NoSchedule@server:0" `
  --k3s-arg "--node-label=workload=argocd@agent:0" `
  --k3s-arg "--node-label=workload=app@agent:1"
```

---

### Step 2: Install ArgoCD (Server-Side Fix for Large CRDs)

Due to large CRD sizes in ArgoCD, it must be installed using `--server-side` to avoid client-size metadata byte limitations:

1. Create the dedicated namespace:
   ```powershell
   kubectl create namespace argocd
   ```
2. Apply the manifest with server-side configurations:
   ```powershell
   kubectl apply -n argocd -f https://githubusercontent.com --server-side --force-conflicts
   ```

---

### Step 3: Access ArgoCD Dashboard & Fetch Password

1. Establish a port-forward tunnel (using port 9090 to avoid local port conflicts):
   ```powershell
   kubectl port-forward svc/argocd-server -n argocd 9090:443
   ```
2. Open your browser and navigate to: `https://127.0.0.1:9090` (Username: `admin`).
3. Decode the initial admin password via PowerShell:
   ```powershell
   \$secret = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
   [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(\$secret))
   ```

---

### Step 4: Deploy the App via GitOps Manifest

Apply the Application controller config to prompt ArgoCD to track your public GitHub repository:

```powershell
kubectl apply -n argocd -f argocd/application.yaml
```

---

## 🔍 Diagnostics & Operational Commands

* **Check Cluster Pods Status:**
  ```powershell
  kubectl get pods
  ```
* **View Real-Time Application Logs:**
  ```powershell
  kubectl logs deployment/skywatch-app --tail=50
  kubectl logs deployment/skywatch-app-worker --tail=50
  ```
* **Verify running image tags (SHA):**
  ```powershell
  kubectl get deployment skywatch-app -o jsonpath='{.spec.template.spec.containers[*].image}'
  ```
