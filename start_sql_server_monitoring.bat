@echo off
echo Starting SQL Server Integration Monitoring...
echo This script will continuously monitor and restart the SQL Server integration if it stops.
echo Press Ctrl+C to stop the monitoring.

:loop
echo.
echo [%date% %time%] Starting SQL Server integration...
python sql_server_integration.py
echo.
echo [%date% %time%] SQL Server integration stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop


