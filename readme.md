להלן קובץ **`README.md`** מפורט ומקצועי המכסה את כל ארכיטקטורת הצינור והתשתיות של פרויקט **SkyWatch**, כולל הוראות התקנה, תפעול, ותחזוקה בסביבת AWS Free Tier:

```markdown
# 🛰️ SkyWatch – Cloud-Native K3s Infrastructure & GitOps Pipeline

ארכיטקטורת ענן מקצה-לקצה (End-to-End) עבור מערכת **SkyWatch**, המבוססת על שרת **AWS EC2 (Free Tier)** בודד. הפרויקט מציג תהליך אוטומטי מלא מהקמת התשתית (IaC) ועד לפריסת האפליקציה בשיטת GitOps.

---

## 📐 ארכיטקטורת המערכת (System Architecture)

המערכת מוקמת בתוך VPC מבודד ב-AWS ומריצה קלאסטר **Single-Node K3s** המאחד את תפקידי ה-Control Plane וה-Worker הצמודים.


```

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

## 🛠️ טכנולוגיות מרכזיות (Tech Stack)

* **Infrastructure as Code (IaC):** Terraform (VPC, Security Groups, EC2, Inventory Export).
* **Configuration Management:** Ansible (Swap Creation, Packages, K3s Bootstrap, Kubeconfig).
* **Container Orchestration:** K3s v1.29.5 (Lightweight Kubernetes).
* **CI/CD Pipeline:** GitHub Actions (Lint → Build & Push Multi-Stage Images to GHCR → Version Tag Bump).
* **Packaging & GitOps:** Helm 3 + ArgoCD v2.11.2 (Auto-sync, Prune, Self-heal).
* **Messaging & Processing:** RabbitMQ 3.13 + Python Workers + Node.js Frontend.

---

## 📂 מבנה התיקיות בפרויקט (Directory Structure)

```text
skywatch/
├── .github/
│   └── workflows/
│       └── ci-cd.yaml          # צינור הבדיקות, הבנייה והדחיפה ל-GHCR
├── terraform/
│   ├── main.tf                 # הגדרות משאבי ה-AWS
│   ├── variables.tf            # משתני תשתית (Region, Instance type, Key)
│   ├── outputs.tf              # פלט IP וייצוא inventory.ini ל-Ansible
│   └── terraform.tfvars        # ערכי משתנים מקומיים
├── ansible/
│   ├── inventory.ini           # מיוצר אוטומטית ע"י Terraform
│   └── setup.yml               # Playbook להגדרת Swap ו-K3s
├── helm/
│   └── skywatch/               # Helm Chart של האפליקציה
│       ├── Chart.yaml
│       └── values.yaml         # הגדרת מגבלות משאבים הדוקות (Requests/Limits)
└── argocd/
    └── application.yaml        # אובייקט Application של ArgoCD

```

---

## ⚡ הוראות התקנה והקמה (Deployment Guide)

### דרישות מוקדמות (Prerequisites)

* להתקין במחשב המקומי: `aws-cli`, `terraform`, `ansible`, `kubectl`, `helm`.
* הוספת SSH Key-Pair פעיל ב-AWS EC2.

---

### שלב 1: הקמת התשתית ב-AWS (Terraform)

1. היכנס/י לתיקיית ה-Terraform:
```bash
cd terraform

```


2. הגדר/י את שם המפתח הציבורי שלך ב-`terraform.tfvars`:
```hcl
key_name      = "your-aws-ssh-key"
instance_type = "t3.micro"
aws_region    = "eu-west-1"

```


3. בצע/י אתחול והקמה:
```bash
terraform init
terraform apply --auto-approve

```



> **תוצאה:** השרת הוקם ב-AWS, וקובץ `ansible/inventory.ini` נוצר אוטומטית עם ה-IP הציבורי.

---

### שלב 2: הגדרת השרת והתקנת K3s (Ansible)

1. היכנס/י לתיקיית Ansible:
```bash
cd ../ansible

```


2. הרץ/י את ה-Playbook ליצירת קובץ ה-Swap והתקנת K3s:
```bash
ansible-playbook -i inventory.ini setup.yml --key-file ~/.ssh/your-aws-ssh-key.pem

```



---

### שלב 3: חיבור ה-kubectl המקומי לקלאסטר

1. העבר/י את קובץ ה-Kubeconfig מהשרת למחשב המקומי:
```bash
scp -i ~/.ssh/your-aws-ssh-key.pem ubuntu@<SERVER_PUBLIC_IP>:/home/ubuntu/.kube/config ~/.kube/skywatch-aws.config

```


2. עדכן/י את ה-IP בקובץ התצורה:
```bash
sed -i '' 's/127.0.0.1/<SERVER_PUBLIC_IP>/g' ~/.kube/skywatch-aws.config

```


3. הגדר/י משתנה סביבה ובדוק/י חיבור:
```bash
export KUBECONFIG=~/.kube/skywatch-aws.config
kubectl get nodes

```



---

### שלב 4: התקנת ArgoCD ופריסת האפליקציה (GitOps)

1. התקן/י את ArgoCD במצב חסכוני:
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f [https://raw.githubusercontent.com/argoproj/argo-cd/v2.11.2/manifests/install.yaml](https://raw.githubusercontent.com/argoproj/argo-cd/v2.11.2/manifests/install.yaml)

```


2. פרוס/י את הגדרת ה-GitOps Application:
```bash
kubectl apply -f argocd/application.yaml

```



---

## 🔒 התאמות מיוחדות ל-AWS Free Tier (`t3.micro`)

עקב המגבלה הקשיחה של **1GB RAM**:

1. **2GB Swap File:** מוקם באופן אוטומטי ע"י Ansible למניעת קריסות זיכרון (`OOMKilled`).
2. **Strict Resource Limits:** כל רכיב ב-Helm (`values.yaml`) מוגבל בצורה קשיחה:
* **Frontend:** Requests `64Mi`, Limits `128Mi`
* **Worker:** Requests `64Mi`, Limits `128Mi`
* **RabbitMQ:** Requests `128Mi`, Limits `256Mi`



---

## 🔍 פקודות דיאגנוסטיקה ותפעול (Troubleshooting)

* **בדיקת סטטוס ה-Pods בקלאסטר:**
```bash
kubectl get pods -A

```


* **בדיקת ניצול זיכרון ו-CPU בזמן אמת:**
```bash
kubectl top pods

```


* **צפייה בלוגים של ה-Worker:**
```bash
kubectl logs -l app=skywatch-worker -f

```


* **בדיקת מצב זיכרון ה-Swap בשרת (SSH):**
```bash
ssh -i ~/.ssh/your-aws-ssh-key.pem ubuntu@<SERVER_PUBLIC_IP> "free -h"

```



```

<FollowUp label="רוצה לשמור את ה-README כקובץ או להוסיף סעיף בדיקות אבטחה (Security Guidelines)?" query="איך להוסיף הנחיות אבטחה ו-Security Groups לקובץ ה-README?"/>

```