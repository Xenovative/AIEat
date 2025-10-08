# AIEat Production Deployment Script for Windows
# Usage: .\deploy.ps1 [-Port 5000]
# Example: .\deploy.ps1 -Port 8080

param(
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 AIEat Production Deployment" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Check Python version
Write-Host "📋 Checking Python version..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Green
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}
Write-Host ""

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "⬆️  Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Green
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ requirements.txt not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "📝 Creating .env from template..." -ForegroundColor Yellow
    
    $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    
    @"
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
SECRET_KEY=$secretKey
"@ | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-Host "✅ .env file created" -ForegroundColor Green
    Write-Host "⚠️  Please edit .env and add your API keys" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env file exists" -ForegroundColor Green
}
Write-Host ""

# Check for database
if (-not (Test-Path "data\restaurants.db")) {
    Write-Host "⚠️  Database not found" -ForegroundColor Yellow
    if (Test-Path "data\openrice_complete.json") {
        Write-Host "📄 JSON file found - database will be auto-generated on first run" -ForegroundColor Green
    } else {
        Write-Host "❌ Neither database nor JSON file found" -ForegroundColor Red
        Write-Host "   Please add data\openrice_complete.json" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Database exists" -ForegroundColor Green
}
Write-Host ""

# Install waitress for production
Write-Host "🦄 Installing Waitress (WSGI server for Windows)..." -ForegroundColor Green
pip install waitress --quiet
Write-Host "✅ Waitress installed" -ForegroundColor Green
Write-Host ""

# Create startup script
Write-Host "⚙️  Creating startup script..." -ForegroundColor Green
$startupScript = @"
@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo Starting AIEat on port $Port...
waitress-serve --host=0.0.0.0 --port=$Port --threads=4 app:app
"@

$startupScript | Out-File -FilePath "start_production.bat" -Encoding ASCII
Write-Host "✅ Startup script created: start_production.bat" -ForegroundColor Green
Write-Host ""

# Create Windows Service installer (optional)
Write-Host "⚙️  Creating Windows Service installer..." -ForegroundColor Green
pip install pywin32 --quiet

$serviceScript = @"
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
from waitress import serve

class AIEatService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AIEat"
    _svc_display_name_ = "AIEat Restaurant Recommendation System"
    _svc_description_ = "AI-powered Hong Kong restaurant recommendation system"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        os.chdir(r'$PWD')
        sys.path.insert(0, r'$PWD')
        from app import app
        serve(app, host='0.0.0.0', port=$Port, threads=4)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AIEatService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AIEatService)
"@

$serviceScript | Out-File -FilePath "windows_service.py" -Encoding UTF8
Write-Host "✅ Windows Service script created: windows_service.py" -ForegroundColor Green
Write-Host ""

Write-Host "================================" -ForegroundColor Green
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 To start the server:" -ForegroundColor Green
Write-Host "   .\start_production.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Or run directly:" -ForegroundColor Green
Write-Host "   waitress-serve --host=0.0.0.0 --port=$Port --threads=4 app:app" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Access your app at:" -ForegroundColor Green
Write-Host "   http://localhost:$Port" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔐 Admin panel:" -ForegroundColor Green
Write-Host "   http://localhost:$Port/admin" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 To install as Windows Service (run as Administrator):" -ForegroundColor Green
Write-Host "   python windows_service.py install" -ForegroundColor Cyan
Write-Host "   python windows_service.py start" -ForegroundColor Cyan
Write-Host ""
