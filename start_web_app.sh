#!/bin/bash

echo "================================================"
echo "🎬 Interactive Anime Video Generator - Web App"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo ""
    echo "Please create a .env file with your API keys:"
    echo "  OPENAI_API_KEY=..."
    echo "  KLING_ACCESS_KEY=..."
    echo "  KLING_SECRET_KEY=..."
    echo ""
    exit 1
fi

# Check if required directories exist
mkdir -p uploads
mkdir -p outputs/web
mkdir -p templates
mkdir -p static

# Check if Python dependencies are installed
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Flask not found. Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo ""
echo "✅ Starting web server..."
echo ""
echo "   Open your browser to: http://localhost:5000"
echo ""
echo "   Press Ctrl+C to stop"
echo ""
echo "================================================"
echo ""

python3 web_app.py

