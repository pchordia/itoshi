#!/bin/bash
# Application setup script - run AFTER uploading code to /var/www/itoshi
# This sets up Python environment, configures services, and starts the app

set -e  # Exit on error

APP_DIR="/var/www/itoshi"

echo "=========================================="
echo "Itoshi Web App - Application Setup"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "$APP_DIR/web_app.py" ]; then
    echo "❌ Error: web_app.py not found in $APP_DIR"
    echo "Please upload your code first!"
    exit 1
fi

cd $APP_DIR

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
pip install gunicorn

# Create .env file if it doesn't exist
if [ ! -f "$APP_DIR/.env" ]; then
    echo "⚙️  Creating .env file..."
    cat > $APP_DIR/.env << 'EOF'
# API Keys (REQUIRED - Fill these in!)
OPENAI_API_KEY=your_openai_key_here
KLING_ACCESS_KEY=your_kling_access_key_here
KLING_SECRET_KEY=your_kling_secret_key_here
KLING_BASE_URL=https://app.klingai.com

# Worker Configuration
ANIME_MAX_WORKERS=10
I2V_MAX_WORKERS=2

# Timeouts
REQUEST_TIMEOUT_SECONDS=120
MAX_RETRIES=6
INITIAL_BACKOFF_SECONDS=1

# Generation Settings
IMAGE_SIZE=auto
VIDEO_DURATION_SECONDS=5
KLING_MODEL=Professional v2.1
ANALYSIS_MODEL=chatgpt-5
EOF
    
    chmod 600 $APP_DIR/.env
    echo ""
    echo "⚠️  IMPORTANT: Edit $APP_DIR/.env and add your API keys!"
    echo "   nano $APP_DIR/.env"
    echo ""
    read -p "Press Enter after you've added your API keys..."
fi

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p $APP_DIR/uploads
mkdir -p $APP_DIR/outputs/web
mkdir -p $APP_DIR/logs
mkdir -p $APP_DIR/templates
mkdir -p $APP_DIR/static

# Set permissions
echo "🔒 Setting permissions..."
chmod 755 $APP_DIR
chmod 755 $APP_DIR/uploads
chmod 755 $APP_DIR/outputs
chmod 755 $APP_DIR/logs

# Configure Supervisor
echo "⚙️  Configuring Supervisor..."
sudo cp $APP_DIR/deploy/supervisor.conf /etc/supervisor/conf.d/itoshi.conf
sudo supervisorctl reread
sudo supervisorctl update

# Configure Nginx
echo "⚙️  Configuring Nginx..."
sudo cp $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/itoshi

# Remove default site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Enable itoshi site
sudo ln -sf /etc/nginx/sites-available/itoshi /etc/nginx/sites-enabled/

# Test nginx config
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

# Restart services
echo "🔄 Starting services..."
sudo supervisorctl start itoshi
sudo systemctl restart nginx

# Check status
echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Service Status:"
sudo supervisorctl status itoshi
sudo systemctl status nginx --no-pager -l
echo ""

# Get public IP
PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || echo "Unable to fetch")

echo "=========================================="
echo "📋 Next Steps:"
echo "=========================================="
echo ""
echo "1. Configure DNS in GoDaddy:"
echo "   - Type: A Record"
echo "   - Name: app"
echo "   - Value: $PUBLIC_IP"
echo "   - TTL: 600"
echo ""
echo "2. Wait 5-10 minutes for DNS propagation"
echo ""
echo "3. Test HTTP access:"
echo "   curl http://app.itoshi.ai"
echo ""
echo "4. Set up SSL certificate:"
echo "   sudo certbot --nginx -d app.itoshi.ai"
echo ""
echo "5. Access your app at: https://app.itoshi.ai"
echo ""
echo "=========================================="
echo "📊 Useful Commands:"
echo "=========================================="
echo ""
echo "View application logs:"
echo "  sudo supervisorctl tail -f itoshi"
echo ""
echo "Restart application:"
echo "  sudo supervisorctl restart itoshi"
echo ""
echo "View Nginx logs:"
echo "  sudo tail -f /var/log/nginx/itoshi_error.log"
echo ""
echo "Update application:"
echo "  cd $APP_DIR && git pull"
echo "  source venv/bin/activate && pip install -r requirements.txt"
echo "  sudo supervisorctl restart itoshi"
echo ""

