@echo off
chcp 65001 >nul
echo ========================================
echo   ICT刷题系统 - 一键启动
echo ========================================
echo.
echo [1/2] 启动 Flask 服务...
start "Flask Server" cmd /k "cd /d E:\ICT刷题系统 && python app.py"

timeout /t 3 /nobreak >nul

echo [2/2] 启动 ngrok 隧道...
start "ngrok Tunnel" cmd /k "D:\ngrok\ngrok.exe http 5000"

echo.
echo ========================================
echo   ✅ 启动完成！
echo ========================================
echo.
echo 请查看 ngrok 窗口的 Forwarding 地址
echo 手机访问该地址即可
echo.
pause