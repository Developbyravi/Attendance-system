# SmartAttend — AWS EC2 Production Deployment Guide

## 1. Instance Specification & Cost Management

- **Selected Instance Type**: `t8i.small` (or `t4g.small` / `t3.small` as regional equivalent)
- **Target OS**: Ubuntu 24.04 LTS (x86_64 or ARM64)
- **vCPU**: 2 vCPUs
- **Memory**: 2 GB – 4 GB RAM
- **Storage**: 30 GB EBS General Purpose (gp3) SSD *(Within AWS Free Tier / Promotional Credit Envelope)*
- **Cost / Credit Strategy**:
  - Utilizing AWS Promotional Credits / Free Tier (750 hours/month of eligible micro/small instances).
  - **No paid enterprise resources will be provisioned without explicit user authorization.**

---

## 2. Memory Optimization (Swap Space)

Deep learning computer vision models (SCRFD-10G ONNX) and OpenCV image decodes can spike in memory during burst processing. For `t8i.small` / `t3.small` instances with 2GB RAM, provision a **2 GB swap file**:

```bash
# Provision 2GB swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Persist across reboots
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 3. Security Group Rules (Firewall)

Configure your AWS EC2 Security Group with strict least-privilege rules:

| Type | Port Range | Protocol | Source | Purpose |
| :--- | :---: | :---: | :--- | :--- |
| **SSH** | `22` | TCP | `YOUR_MY_IP/32` | Administrative shell access (never open to `0.0.0.0/0`) |
| **HTTP** | `80` | TCP | `0.0.0.0/0` | Public Web traffic & ACME SSL challenges |
| **HTTPS** | `443` | TCP | `0.0.0.0/0` | Secure Web traffic & API ingestion |
| **Backend API** | `8002` | TCP | `0.0.0.0/0` (or reverse proxied via Nginx) | Direct hardware/kiosk access if Nginx is bypassed |

---

## 4. Step-by-Step Installation Commands

```bash
# 1. Connect to EC2
ssh -i "your-key.pem" ubuntu@ec2-xx-xx-xx-xx.compute-1.amazonaws.com

# 2. Clone Repository
git clone https://github.com/Developbyravi/Attendance-system.git
cd Attendance-system

# 3. Configure Production Environment
cp backend2/.env.example deployment/.env
nano deployment/.env
# Update:
#   APP_ENV=production
#   SECRET_KEY=generate_a_random_64_char_key
#   DATABASE_URL=postgresql://user:pass@host:5432/dbname
#   CORS_ORIGINS=https://smartattend.vercel.app

# 4. Run Automated Deployment
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

---

## 5. SSL / TLS Certificate Provisioning (Let's Encrypt)

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

---

## 6. Health & Diagnostics Check

Verify your running instance:
```bash
# Probe backend health
curl -f http://localhost:8002/api/health
```
