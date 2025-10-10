# 🚀 Quick Deployment Guide - app.itoshi.ai

## TL;DR - Get Running in 30 Minutes

### 1. Launch EC2 Instance (5 min)

**AWS Console → EC2 → Launch Instance:**
- **Name**: `itoshi-app`
- **OS**: Ubuntu Server 22.04 LTS
- **Instance**: `t3.medium` (2 vCPU, 4GB RAM)
- **Storage**: 30GB gp3
- **Security Group**: 
  - SSH (22) - Your IP
  - HTTP (80) - 0.0.0.0/0
  - HTTPS (443) - 0.0.0.0/0
- **Download key pair** (e.g., `itoshi-key.pem`)

### 2. Connect to Server (1 min)

```bash
chmod 400 itoshi-key.pem
ssh -i itoshi-key.pem ubuntu@YOUR_EC2_IP
```

### 3. Setup Server (2 min)

On EC2:
```bash
# Download and run setup script
curl -o setup.sh https://raw.githubusercontent.com/YOUR_REPO/deploy/setup_server.sh
bash setup.sh
```

Or manually:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3-pip python3-venv nginx supervisor git
sudo mkdir -p /var/www/itoshi
sudo chown ubuntu:ubuntu /var/www/itoshi
```

### 4. Upload Code (3 min)

**From your local machine:**
```bash
cd /path/to/itoshi
scp -i itoshi-key.pem -r * ubuntu@YOUR_EC2_IP:/var/www/itoshi/
```

Or clone from git:
```bash
cd /var/www/itoshi
git clone YOUR_REPO_URL .
```

### 5. Configure App (5 min)

On EC2:
```bash
cd /var/www/itoshi

# Setup Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn

# Create .env file
nano .env
```

Paste your keys:
```
OPENAI_API_KEY=sk-...
KLING_ACCESS_KEY=...
KLING_SECRET_KEY=...
```

Save (Ctrl+O, Enter, Ctrl+X)

```bash
chmod 600 .env
mkdir -p uploads outputs/web logs
```

### 6. Configure Services (5 min)

```bash
# Copy config files
sudo cp deploy/supervisor.conf /etc/supervisor/conf.d/itoshi.conf
sudo cp deploy/nginx.conf /etc/nginx/sites-available/itoshi
sudo ln -s /etc/nginx/sites-available/itoshi /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Start services
sudo supervisorctl reread && sudo supervisorctl update
sudo supervisorctl start itoshi
sudo nginx -t && sudo systemctl restart nginx
```

### 7. Configure DNS (3 min)

**GoDaddy → DNS Management:**
- Type: **A Record**
- Name: **app**
- Value: **YOUR_EC2_IP** (from AWS console)
- TTL: **600**

Wait 5-10 minutes for DNS propagation.

### 8. Test (1 min)

```bash
curl http://app.itoshi.ai
```

Should return HTML!

### 9. Enable HTTPS (5 min)

On EC2:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d app.itoshi.ai
```

Follow prompts, choose "Redirect HTTP to HTTPS".

### 10. Done! 🎉

Visit: **https://app.itoshi.ai**

---

## One-Command Setup (After Code Upload)

```bash
cd /var/www/itoshi && bash deploy/setup_app.sh
```

---

## Useful Commands

```bash
# View logs
sudo supervisorctl tail -f itoshi

# Restart app
sudo supervisorctl restart itoshi

# Update app
cd /var/www/itoshi && git pull
source venv/bin/activate && pip install -r requirements.txt
sudo supervisorctl restart itoshi

# View nginx logs
sudo tail -f /var/log/nginx/itoshi_error.log
```

---

## Cost

- **~$42/month** (t3.medium + storage + data transfer)
- Plus API usage costs (OpenAI + Kling)

---

## Troubleshooting

**App won't start?**
```bash
sudo supervisorctl tail itoshi stderr
```

**Nginx error?**
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

**Can't connect?**
- Check EC2 Security Group has ports 80/443 open
- Verify DNS with: `dig app.itoshi.ai`

---

See `DEPLOYMENT_GUIDE.md` for full details!

