#!/bin/bash
# Setup script for deploying Itoshi web app on Ubuntu 22.04
# Run this after connecting to your EC2 instance via SSH

set -e  # Exit on error

echo "=========================================="
echo "Itoshi Web App - Server Setup Script"
echo "=========================================="
echo ""

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
sudo apt install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    nginx \
    supervisor \
    git \
    curl \
    ufw

# Configure firewall
echo "🔒 Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw status

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /var/www/itoshi
sudo chown $USER:$USER /var/www/itoshi

# Note: At this point, you need to upload your code
echo ""
echo "=========================================="
echo "⚠️  NEXT STEPS:"
echo "=========================================="
echo ""
echo "1. Upload your code to /var/www/itoshi"
echo "   From your local machine, run:"
echo "   scp -r /path/to/itoshi/* ubuntu@YOUR_EC2_IP:/var/www/itoshi/"
echo ""
echo "2. Or clone from git:"
echo "   cd /var/www/itoshi"
echo "   git clone YOUR_REPO_URL ."
echo ""
echo "3. Then run: bash /var/www/itoshi/deploy/setup_app.sh"
echo ""

