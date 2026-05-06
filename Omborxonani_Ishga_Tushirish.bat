@echo off
title Omborxona Tizimi Serveri
color 0A
echo ===================================================
echo   Omborxona Tizimi serveri ishga tushirilmoqda...
echo ===================================================
echo.
echo ILTIMOS, BU OYNANI YOPMANG!
echo Dastur ishlashi uchun ushbu qora oyna ochiq turishi shart.
echo.
echo Brauzer avtomatik ravishda ochiladi...
timeout /t 2 /nobreak > nul
start http://127.0.0.1:5000
py app.py
pause
