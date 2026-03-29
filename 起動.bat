@echo off
cd /d "%~dp0"
echo STS2 敵図鑑 を起動しています...
start cmd /k "npm run dev"
timeout /t 6 /nobreak > nul
start http://localhost:3000
