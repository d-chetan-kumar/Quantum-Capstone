@echo off
title Quantum Fraud Detection - Live Deployment
echo ========================================================
echo  Starting Quantum Fraud Detection Platform (Live Mode)
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Closing any previous instances...
taskkill /f /im cloudflared.exe 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq QuantumBackend*" 2>nul

echo [2/3] Launching unified FastAPI server (Frontend + Backend + Database)...
start "QuantumBackend" /min backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend

timeout /t 3 /nobreak >nul

echo [3/3] Launching public tunnel...
echo.
echo ========================================================
echo  LOOK BELOW FOR YOUR PUBLIC HTTPS LINK (trycloudflare.com)
echo  Keep this window open while sharing your link!
echo ========================================================
echo.

.\cloudflared.exe tunnel --url http://127.0.0.1:8000
