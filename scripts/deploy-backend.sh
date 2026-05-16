#!/bin/bash
# deploy-backend.sh
# Run this on the EC2 instance to pull latest backend code and restart the service.
# Usage: bash deploy-backend.sh

set -e

REPO_DIR=~/polynovea_acquisition
SERVICE=polynovea

echo "── Pulling latest code ──────────────────────────────"
cd "$REPO_DIR"
git pull origin master

echo "── Installing/updating dependencies ─────────────────"
cd App/backend
pip install -r requirements.txt --quiet --break-system-packages

echo "── Restarting service ───────────────────────────────"
sudo systemctl restart "$SERVICE"
sleep 2
sudo systemctl status "$SERVICE" --no-pager

echo ""
echo "✓ Deploy complete. Backend is live at http://$(curl -s ifconfig.me):8000"
