# 🚀 AIEat Deployment Guide

## Quick Start

### Linux/Mac
```bash
chmod +x deploy.sh
./deploy.sh 5000
```

### Windows
```powershell
.\deploy.ps1 -Port 5000
```

---

## Deployment Options

### 1. **Linux with Systemd (Recommended)**

The deployment script automatically:
- Creates virtual environment
- Installs dependencies
- Sets up systemd service
- Starts the app with Gunicorn

**Commands:**
```bash
# Deploy on default port (5000)
./deploy.sh

# Deploy on custom port
./deploy.sh 8080

# Manage service
sudo systemctl status aieat
sudo systemctl restart aieat
sudo systemctl stop aieat
sudo systemctl start aieat

# View logs
sudo journalctl -u aieat -f
```

---

### 2. **Windows with Waitress**

**Option A: Run as Script**
```powershell
# Deploy
.\deploy.ps1 -Port 5000

# Start server
.\start_production.bat
```

**Option B: Install as Windows Service**
```powershell
# Run as Administrator
python windows_service.py install
python windows_service.py start

# Manage service
python windows_service.py stop
python windows_service.py restart
python windows_service.py remove
```

---

### 3. **Docker Deployment**

```bash
# Build image
docker build -t aieat .

# Run container
docker run -d -p 5000:5000 --name aieat \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  aieat

# View logs
docker logs -f aieat
```

---

### 4. **Manual Production Setup**

**Linux (Gunicorn):**
```bash
# Install
pip install gunicorn

# Run
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 production:app
```

**Windows (Waitress):**
```bash
# Install
pip install waitress

# Run
waitress-serve --host=0.0.0.0 --port=5000 --threads=4 production:app
```

---

## Environment Configuration

### Required `.env` File

```env
# AI Service (choose one)
AI_SERVICE=ollama  # or 'openrouter' or 'openai'

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# OpenRouter Configuration (optional)
OPENROUTER_API_KEY=your_key_here

# OpenAI Configuration (optional)
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# Admin Panel
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_this_password
SECRET_KEY=generate_random_secret_key
```

---

## Nginx Reverse Proxy (Optional)

### Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files (optional optimization)
    location /static {
        alias /path/to/aieat/static;
        expires 30d;
    }
}
```

### Enable and Restart
```bash
sudo ln -s /etc/nginx/sites-available/aieat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## SSL/HTTPS with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

---

## Performance Tuning

### Gunicorn Workers
```bash
# Formula: (2 x CPU cores) + 1
# For 4 cores: 9 workers
gunicorn -w 9 -b 0.0.0.0:5000 production:app
```

### Waitress Threads
```bash
# For Windows, use threads instead of workers
waitress-serve --threads=8 --port=5000 production:app
```

---

## Monitoring

### Check Service Status
```bash
# Linux
sudo systemctl status aieat
curl http://localhost:5000/health

# Windows
sc query AIEat
curl http://localhost:5000/health
```

### View Logs
```bash
# Linux (systemd)
sudo journalctl -u aieat -f

# Linux (manual)
tail -f logs/app.log

# Windows
Get-Content logs\app.log -Wait
```

---

## Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u aieat -xe

# Check if port is in use
sudo lsof -i :5000

# Test manually
source venv/bin/activate
python app.py
```

### Database Issues
```bash
# Database will auto-generate from JSON on first run
# If issues persist, delete and regenerate:
rm data/restaurants.db
python app.py
```

### Permission Issues
```bash
# Fix ownership
sudo chown -R $USER:$USER /path/to/aieat

# Fix permissions
chmod +x deploy.sh
chmod 644 .env
```

---

## Security Checklist

- [ ] Change default admin password in `.env`
- [ ] Generate strong `SECRET_KEY`
- [ ] Use HTTPS in production
- [ ] Set up firewall rules
- [ ] Keep dependencies updated
- [ ] Regular backups of database
- [ ] Monitor logs for suspicious activity
- [ ] Use environment variables for secrets
- [ ] Disable debug mode in production

---

## Backup & Restore

### Backup
```bash
# Database
cp data/restaurants.db backups/restaurants_$(date +%Y%m%d).db

# Full backup
tar -czf aieat_backup_$(date +%Y%m%d).tar.gz \
  data/ .env requirements.txt
```

### Restore
```bash
# Extract backup
tar -xzf aieat_backup_20250108.tar.gz

# Restart service
sudo systemctl restart aieat
```

---

## Updating

```bash
# Pull latest code
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart aieat
```

---

## Support

- **GitHub Issues**: [Your Repo URL]
- **Documentation**: [Your Docs URL]
- **Email**: [Your Email]
