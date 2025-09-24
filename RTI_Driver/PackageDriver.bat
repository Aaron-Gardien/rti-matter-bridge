@echo off
:start
set /p DriverName=Enter Output Driver Name:
packagedriver -o %DriverName%.RTIDRIVER||goto start
pause