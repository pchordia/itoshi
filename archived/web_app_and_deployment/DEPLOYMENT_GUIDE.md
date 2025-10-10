# 🚀 Deployment Guide: app.itoshi.ai on AWS

Complete guide to deploy your Interactive Anime Video Generator web app to AWS with your custom domain.

## 📋 Prerequisites

- ✅ AWS Account
- ✅ GoDaddy domain (itoshi.ai)
- ✅ API keys (OpenAI, Kling)

## 🏗️ Architecture Overview

We'll use:
- **AWS EC2** - Host the Flask application
- **Nginx** - Reverse proxy and serve static files
- **Gunicorn** - Production WSGI server
- **SSL/TLS** - Let's Encrypt for HTTPS
- **Route 53 or GoDaddy DNS** - Point app.itoshi.ai to EC2

---

## Option 1: AWS EC2 (Recommended - Full Control)

### Step 1: Launch EC2 Instance

1. **Go to AWS EC2 Console**
   - Region: Choose closest to your users (e.g., us-east-1)
   - Click "Launch Instance"

2. **Configure Instance**
   - **Name**: `itoshi-anime-generator`
   - **OS**: Ubuntu Server 22.04 LTS (Free tier eligible)
   - **Instance type**: `t3.medium` or `t3.large` (need decent CPU/memory)
     - t3.medium: 2 vCPU, 4GB RAM (~$30/month)
     - t3.large: 2 vCPU, 8GB RAM (~$60/month)
   - **Key pair**: Create new or use existing (download .pem file)
   - **Storage**: 30GB gp3 SSD minimum

3. **Security Group (Firewall)**
   ```
   Inbound Rules:
   - SSH (22) - Your IP only
   - HTTP (80) - 0.0.0.0/0
   - HTTPS (443) - 0.0.0.0/0
   ```

4. **Launch Instance** and note the Public IP

### Step 2: Connect to EC2

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

### Step 3: Set Up Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and essentials
sudo apt install -y python3.10 python3-pip python3-venv nginx git

# Install Supervisor (process manager)
sudo apt install -y supervisor

# Create application directory
sudo mkdir -p /var/www/itoshi
sudo chown ubuntu:ubuntu /var/www/itoshi
cd /var/www/itoshi

# Clone or upload your code
# Option A: If you have a git repo
git clone https://your-repo-url.git .

# Option B: Upload files via SCP from your local machine
# (Run this from your local machine, not EC2)
# scp -i your-key.pem -r /path/to/itoshi/* ubuntu@YOUR_EC2_IP:/var/www/itoshi/
```

### Step 4: Set Up Python Environment

```bash
cd /var/www/itoshi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create .env file
nano .env
```

Paste your API keys:
```bash
OPENAI_API_KEY=sk-...
KLING_ACCESS_KEY=...
KLING_SECRET_KEY=...
KLING_BASE_URL=https://app.klingai.com

ANIME_MAX_WORKERS=10
I2V_MAX_WORKERS=2
REQUEST_TIMEOUT_SECONDS=120
MAX_RETRIES=6
INITIAL_BACKOFF_SECONDS=1

IMAGE_SIZE=auto
VIDEO_DURATION_SECONDS=5
KLING_MODEL=Professional v2.1
ANALYSIS_MODEL=chatgpt-5
```

Save and exit (Ctrl+O, Enter, Ctrl+X)

```bash
# Set proper permissions
chmod 600 .env

# Create necessary directories
mkdir -p uploads outputs/web logs
```

### Step 5: Configure Gunicorn

Create a Gunicorn config file:

```bash
nano gunicorn_config.py
```

```python
# gunicorn_config.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 300  # 5 minutes for long-running requests
keepalive = 5
errorlog = "/var/www/itoshi/logs/gunicorn-error.log"
accesslog = "/var/www/itoshi/logs/gunicorn-access.log"
loglevel = "info"
```

Test Gunicorn:
```bash
source venv/bin/activate
gunicorn -c gunicorn_config.py web_app:app
# Press Ctrl+C to stop
```

### Step 6: Configure Supervisor (Process Manager)

```bash
sudo nano /etc/supervisor/conf.d/itoshi.conf
```

```ini
[program:itoshi]
directory=/var/www/itoshi
command=/var/www/itoshi/venv/bin/gunicorn -c gunicorn_config.py web_app:app
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/www/itoshi/logs/supervisor-error.log
stdout_logfile=/var/www/itoshi/logs/supervisor-output.log
environment=PATH="/var/www/itoshi/venv/bin"
```

Start the application:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start itoshi
sudo supervisorctl status itoshi
```

### Step 7: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/itoshi
```

```nginx
server {
    listen 80;
    server_name app.itoshi.ai;
    
    client_max_body_size 20M;  # Allow large file uploads
    
    # Redirect to HTTPS (after SSL is set up)
    # return 301 https://$server_name$request_uri;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    location /static {
        alias /var/www/itoshi/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /outputs {
        alias /var/www/itoshi/outputs/web;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/itoshi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 8: Configure DNS (GoDaddy)

**Option A: Use GoDaddy DNS (Simpler)**

1. Go to GoDaddy → My Products → DNS
2. Add an A Record:
   - **Type**: A
   - **Name**: `app` (for app.itoshi.ai)
   - **Value**: Your EC2 Public IP
   - **TTL**: 600 seconds

**Option B: Use AWS Route 53 (More Features)**

1. Create hosted zone in Route 53 for itoshi.ai
2. Create A record for app.itoshi.ai pointing to EC2 IP
3. Update nameservers in GoDaddy to Route 53 nameservers

Wait 5-10 minutes for DNS propagation, then test:
```bash
# From your local machine
curl http://app.itoshi.ai
```

### Step 9: Set Up SSL (HTTPS)

Install Certbot:
```bash
sudo apt install -y certbot python3-certbot-nginx
```

Get SSL certificate:
```bash
sudo certbot --nginx -d app.itoshi.ai
```

Follow prompts:
- Enter email address
- Agree to terms
- Choose "Redirect HTTP to HTTPS" (option 2)

Test auto-renewal:
```bash
sudo certbot renew --dry-run
```

Now uncomment the HTTPS redirect in your nginx config if Certbot didn't add it.

### Step 10: Test Your Deployment

Visit: **https://app.itoshi.ai**

Check logs:
```bash
# Application logs
sudo supervisorctl tail -f itoshi

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Gunicorn logs
tail -f /var/www/itoshi/logs/gunicorn-error.log
```

---

## Option 2: AWS Elastic Beanstalk (Easier but Less Control)

### Step 1: Prepare Application

Create `requirements.txt` with all dependencies (already done).

Create `.ebignore`:
```
*.pyc
__pycache__/
venv/
.env.local
outputs/
uploads/
logs/
*.pem
.DS_Store
```

### Step 2: Install EB CLI

```bash
pip install awsebcli
```

### Step 3: Initialize EB Application

```bash
cd /path/to/itoshi
eb init -p python-3.10 itoshi-app --region us-east-1
```

### Step 4: Create Environment

```bash
eb create itoshi-prod
```

### Step 5: Set Environment Variables

```bash
eb setenv \
  OPENAI_API_KEY=sk-... \
  KLING_ACCESS_KEY=... \
  KLING_SECRET_KEY=... \
  ANALYSIS_MODEL=chatgpt-5
```

### Step 6: Configure Custom Domain

1. In EB console, go to your environment
2. Configuration → Load balancer → Add listener (443, HTTPS)
3. Upload SSL certificate or use AWS Certificate Manager
4. In GoDaddy, create CNAME: `app` → your EB URL

### Step 7: Deploy

```bash
eb deploy
eb open
```

---

## Option 3: Docker + AWS ECS/Fargate (Most Scalable)

### Step 1: Create Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p uploads outputs/web logs

# Expose port
EXPOSE 8000

# Run with gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "--timeout", "300", "web_app:app"]
```

### Step 2: Build and Push to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name itoshi-app

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t itoshi-app .

# Tag and push
docker tag itoshi-app:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/itoshi-app:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/itoshi-app:latest
```

### Step 3: Create ECS Task Definition

Use AWS ECS console to create a Fargate task with your ECR image.

---

## 🔒 Security Best Practices

1. **Never commit .env file** - Add to .gitignore
2. **Use AWS Secrets Manager** for production secrets
3. **Enable CloudWatch** for monitoring
4. **Set up CloudFront CDN** for static assets
5. **Enable AWS WAF** for DDoS protection
6. **Regular security updates**: `sudo apt update && sudo apt upgrade`
7. **Restrict SSH access** to your IP only
8. **Use IAM roles** instead of access keys when possible

---

## 📊 Monitoring & Maintenance

### Check Application Status
```bash
sudo supervisorctl status itoshi
sudo systemctl status nginx
```

### View Logs
```bash
# Application logs
sudo supervisorctl tail -f itoshi

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Restart application
sudo supervisorctl restart itoshi

# Restart nginx
sudo systemctl restart nginx
```

### Update Application
```bash
cd /var/www/itoshi
git pull  # or upload new files
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart itoshi
```

---

## 💰 Cost Estimates (AWS)

| Resource | Type | Monthly Cost |
|----------|------|--------------|
| EC2 Instance | t3.medium | ~$30 |
| EC2 Instance | t3.large | ~$60 |
| Storage (30GB) | gp3 SSD | ~$3 |
| Data Transfer | 100GB out | ~$9 |
| Route 53 (optional) | Hosted zone | $0.50 |
| **Total (medium)** | | **~$42/month** |
| **Total (large)** | | **~$72/month** |

Note: API costs (OpenAI, Kling) are separate and depend on usage.

---

## 🚨 Troubleshooting

### Application won't start
```bash
# Check logs
sudo supervisorctl tail itoshi stderr

# Check if port 8000 is in use
sudo netstat -tlnp | grep 8000

# Manually test gunicorn
cd /var/www/itoshi
source venv/bin/activate
gunicorn -c gunicorn_config.py web_app:app
```

### Nginx errors
```bash
# Test config
sudo nginx -t

# Check error log
sudo tail -f /var/log/nginx/error.log
```

### File upload fails
```bash
# Check permissions
ls -la /var/www/itoshi/uploads

# Fix permissions
sudo chown -R ubuntu:www-data /var/www/itoshi/uploads
sudo chmod -R 775 /var/www/itoshi/uploads
```

### Out of disk space
```bash
# Check disk usage
df -h

# Clean old outputs
find /var/www/itoshi/outputs/web -type f -mtime +7 -delete
```

---

## 🎯 Recommended: EC2 with t3.medium

For your use case, I recommend **Option 1 (EC2 with t3.medium)**:
- ✅ Full control over resources
- ✅ Good performance for AI workloads
- ✅ Reasonable cost (~$42/month)
- ✅ Easy to scale up if needed
- ✅ Can handle 5-10 concurrent users

---

## 📞 Need Help?

Common issues and solutions are in the Troubleshooting section above. For AWS-specific issues, check AWS documentation or CloudWatch logs.

**Next Steps:**
1. Launch EC2 instance
2. Follow steps 2-10 above
3. Test at https://app.itoshi.ai
4. Monitor for 24 hours
5. Scale as needed!

