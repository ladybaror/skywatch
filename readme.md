# 🛰️ SkyWatch – Cloud-Native K3s Infrastructure & GitOps Pipeline

An end-to-end cloud infrastructure and automation setup for the **SkyWatch** application, built on a single **AWS EC2 (Free Tier)** instance. This project demonstrates a fully automated pipeline starting from Infrastructure as Code (IaC) up to GitOps-driven deployment.

---

## 📐 System Architecture

The infrastructure is provisioned inside an isolated AWS VPC, hosting a **Single-Node K3s Cluster** that combines both Control Plane and Worker roles on a single server.

```text
+----------------------------------------------------------------------------------+
| AWS EC2 (t3.micro - Free Tier) - Ubuntu 22.04                                     |
| 1GB Physical RAM + 2GB Swap File                                                 |
|                                                                                  |
|  +----------------------------------------------------------------------------+  |
|  | K3s Lightweight Kubernetes Cluster                                         |  |
|  |                                                                            |  |
|  | [Namespace: default / skywatch]                                            |  |
|  |  ├── 🌐 SkyWatch Frontend (Pod)                                            |  |
|  |  ├── 🐰 RabbitMQ 3.13-management (StatefulSet/Pod)                         |  |
|  |  └── ⚙️  SkyWatch Worker (Pod)                                              |  |
|  |                                                                            |  |
|  | [Namespace: argocd]                                                        |  |
|  |  └── 🔄 ArgoCD v2.11.2 (GitOps Controller - Sync from Git)                 |  |
|  +----------------------------------------------------------------------------+  |
+----------------------------------------------------------------------------------+
                                      ▲
                                      │ Auto-Sync / Deployment
                                      │
               +----------------------+----------------------+
               |                                             |
    +--------------------+                        +--------------------+
    | GitHub Repository  |                        |  GitHub Container  |
    | (Helm Charts &     |                        |  Registry (GHCR)   |
    | Manifests)         |                        |  (Docker Images)   |
    +--------------------+                        +--------------------+
```

---

## 🛠️ Tech Stack

* **Infrastructure as Code (IaC):** Terraform (VPC, Security Groups, EC2, Ansible Inventory Export).
* **Configuration Management:** Ansible (Swap File Creation, System Packages, K3s Bootstrap, Kubeconfig Setup).
* **Container Orchestration:** K3s v1.29.5 (Lightweight Kubernetes).
* **CI/CD Pipeline:** GitHub Actions (Lint → Multi-Stage Docker Build & Push to GHCR → Version Tag Bump).
* **Packaging & GitOps:** Helm 3 + ArgoCD v2.11.2 (Automated Sync, Pruning, Self-healing).
* **Messaging & Processing:** RabbitMQ 3.13 + Python Workers + Node.js Frontend.

---

## 📂 Directory Structure

```text
skywatch/
├── .github/
│   └── workflows/
│       └── ci-cd.yaml          # CI/CD Pipeline for Testing, Building, and Pushing to GHCR
├── terraform/
│   ├── main.tf                 # AWS Infrastructure Resource Definitions
│   ├── variables.tf            # Infrastructure Variables (Region, Instance Type, Key Name)
│   ├── outputs.tf              # Public IP Output & Automatic inventory.ini Generation
│   └── terraform.tfvars        # Local Variable Values
├── ansible/
│   ├── inventory.ini           # Generated Automatically by Terraform
│   └── setup.yml               # Ansible Playbook for Swap & K3s Bootstrap
├── helm/
│   └── skywatch/               # Application Helm Chart
│       ├── Chart.yaml
│       └── values.yaml         # Resource Constraints (Requests / Limits)
└── argocd/
    └── application.yaml        # ArgoCD Application Manifest
```

---

## ⚡ Deployment Guide

### Prerequisites
* Installed on local machine: `aws-cli`, `terraform`, `ansible`, `kubectl`, `helm`.
* Active SSH Key-Pair uploaded to AWS EC2.

---

### Step 1: Provision Infrastructure with Terraform

1. Navigate to the `terraform` directory:
   ```bash
   cd terraform
   ```
2. Configure your SSH Key Name in `terraform.tfvars`:
   ```hcl
   key_name      = "your-aws-ssh-key"
   instance_type = "t3.micro"
   aws_region    = "eu-west-1"
   ```
3. Initialize and apply the configuration:
   ```bash
   terraform init
   terraform apply --auto-approve
   ```
> **Result:** EC2 Instance and VPC resources are created in AWS, and `ansible/inventory.ini` is generated automatically.

---

### Step 2: Configure Server & Install K3s with Ansible

1. Navigate to the `ansible` directory:
   ```bash
   cd ../ansible
   ```
2. Run the Ansible Playbook to configure Swap and install K3s:
   ```bash
   ansible-playbook -i inventory.ini setup.yml --key-file ~/.ssh/your-aws-ssh-key.pem
   ```

---

### Step 3: Connect Local `kubectl` to Remote Cluster

1. Fetch the `kubeconfig` file from the EC2 instance to your local machine:
   ```bash
   scp -i ~/.ssh/your-aws-ssh-key.pem ubuntu@<SERVER_PUBLIC_IP>:/home/ubuntu/.kube/config ~/.kube/skywatch-aws.config
   ```
2. Update the cluster server IP address inside the config file:
   ```bash
   sed -i '' 's/127.0.0.1/<SERVER_PUBLIC_IP>/g' ~/.kube/skywatch-aws.config
   ```
3. Set the `KUBECONFIG` environment variable and verify connectivity:
   ```bash
   export KUBECONFIG=~/.kube/skywatch-aws.config
   kubectl get nodes
   ```

---

### Step 4: Install ArgoCD & Deploy Application (GitOps)

1. Install ArgoCD in lightweight mode:
   ```bash
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.11.2/manifests/install.yaml
   ```
2. Deploy the ArgoCD GitOps Application manifest:
   ```bash
   kubectl apply -f argocd/application.yaml
   ```

---

## 🔒 AWS Free Tier Optimizations (`t3.micro`)

Due to strict **1GB Physical RAM** constraints:

1. **2GB Swap File:** Automatically created by Ansible to prevent out-of-memory (`OOMKilled`) crashes.
2. **Strict Resource Limits:** Enforced via Helm `values.yaml`:
   * **Frontend:** Requests `64Mi`, Limits `128Mi`
   * **Worker:** Requests `64Mi`, Limits `128Mi`
   * **RabbitMQ:** Requests `128Mi`, Limits `256Mi`

---

## 🔍 Diagnostics & Operational Commands

* **Check Cluster Pods Status:**
  ```bash
  kubectl get pods -A
  ```
* **Monitor Resource Usage (CPU/RAM):**
  ```bash
  kubectl top pods
  ```
* **View Worker Logs:**
  ```bash
  kubectl logs -l app=skywatch-worker -f
  ```
* **Check Swap Memory Status on EC2:**
  ```bash
  ssh -i ~/.ssh/your-aws-ssh-key.pem ubuntu@<SERVER_PUBLIC_IP> "free -h"
  ```