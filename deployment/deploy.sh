#!/bin/bash
# ==============================================================================
# SmartAttend — AWS EC2 Production Deployment Script
# Targets: Ubuntu 24.04 LTS / t8i.small / t3.small / t3.medium
# ==============================================================================

set -e

echo "=================================================="
echo " Starting SmartAttend Deployment on AWS EC2"
echo "=================================================="

# 1. Update OS packages
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 2. Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "[DOCKER] Installing Docker Engine..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
fi

# 3. Pull latest code
echo "[GIT] Fetching latest production release..."
git pull origin main

# 4. Check for production environment file
if [ ! -f "deployment/.env" ]; then
    echo "[WARNING] deployment/.env not found! Copying from template..."
    cp deployment/ENVIRONMENT_VARIABLES.md deployment/.env
    echo "[ACTION REQUIRED] Edit deployment/.env before starting services."
    exit 1
fi

# 5. Build and launch Docker containers
echo "[DOCKER COMPOSE] Rebuilding and launching containers..."
cd deployment
docker compose down --remove-orphans || true
docker compose up -d --build

# 6. Verify health
echo "[HEALTH CHECK] Waiting for FastAPI to report healthy..."
sleep 10
docker compose ps
curl -f http://localhost:8002/api/health || {
    echo "[ERROR] Health check failed!"
    exit 1
}

echo "=================================================="
echo " SmartAttend Backend deployed successfully!"
echo " Swagger UI: http://YOUR_SERVER_IP:8002/docs"
echo "=================================================="
