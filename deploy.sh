#!/bin/bash

# AIEat Production Deployment Script
# Usage: ./deploy.sh [port]
# Example: ./deploy.sh 8080

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default port
PORT=${1:-5000}

echo -e "${GREEN}🚀 AIEat Production Deployment${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}⚠️  Warning: Running as root. Consider using a non-root user.${NC}"
fi

# Check Python version
echo -e "${GREEN}📋 Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ Found: $PYTHON_VERSION${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${GREEN}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo -e "${GREEN}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${GREEN}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo -e "${GREEN}📥 Installing dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo -e "${YELLOW}📝 Creating .env from template...${NC}"
    cat > .env << EOF
# AI Service Configuration
AI_SERVICE=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# OpenRouter Configuration (optional)
OPENROUTER_API_KEY=

# OpenAI Configuration (optional)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Admin Panel Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env and add your API keys${NC}"
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi
echo ""

# Check for database
if [ ! -f "data/restaurants.db" ]; then
    echo -e "${YELLOW}⚠️  Database not found${NC}"
    if [ -f "data/openrice_complete.json" ]; then
        echo -e "${GREEN}📄 JSON file found - database will be auto-generated on first run${NC}"
    else
        echo -e "${RED}❌ Neither database nor JSON file found${NC}"
        echo -e "${RED}   Please add data/openrice_complete.json${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Database exists${NC}"
fi
echo ""

# Install gunicorn for production
echo -e "${GREEN}🦄 Installing Gunicorn (WSGI server)...${NC}"
pip install gunicorn > /dev/null 2>&1
echo -e "${GREEN}✅ Gunicorn installed${NC}"
echo ""

# Create systemd service file
echo -e "${GREEN}⚙️  Creating systemd service...${NC}"
SERVICE_FILE="/etc/systemd/system/aieat.service"
CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)

sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=AIEat - Hong Kong Restaurant Recommendation System
After=network.target

[Service]
Type=notify
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/venv/bin"
ExecStart=$CURRENT_DIR/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --error-logfile - app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Service file created at $SERVICE_FILE${NC}"
echo ""

# Reload systemd
echo -e "${GREEN}🔄 Reloading systemd...${NC}"
sudo systemctl daemon-reload

# Enable and start service
echo -e "${GREEN}🚀 Starting AIEat service on port $PORT...${NC}"
sudo systemctl enable aieat
sudo systemctl restart aieat

# Wait a moment for service to start
sleep 2

# Check service status
if sudo systemctl is-active --quiet aieat; then
    echo -e "${GREEN}✅ AIEat is running!${NC}"
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "${GREEN}📍 Access your app at:${NC}"
    echo -e "${GREEN}   http://localhost:$PORT${NC}"
    echo -e "${GREEN}   http://$(hostname -I | awk '{print $1}'):$PORT${NC}"
    echo ""
    echo -e "${GREEN}🔐 Admin panel:${NC}"
    echo -e "${GREEN}   http://localhost:$PORT/admin${NC}"
    echo ""
    echo -e "${GREEN}📊 Useful commands:${NC}"
    echo -e "${GREEN}   sudo systemctl status aieat    ${NC}# Check status"
    echo -e "${GREEN}   sudo systemctl restart aieat   ${NC}# Restart service"
    echo -e "${GREEN}   sudo systemctl stop aieat      ${NC}# Stop service"
    echo -e "${GREEN}   sudo journalctl -u aieat -f   ${NC}# View logs"
    echo ""
else
    echo -e "${RED}❌ Service failed to start${NC}"
    echo -e "${RED}Check logs with: sudo journalctl -u aieat -xe${NC}"
    exit 1
fi
EOF
