@echo off
echo Stopping all services...

taskkill /F /IM java.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM mongod.exe >nul 2>&1

echo DONE
pause