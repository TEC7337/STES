@echo off
REM Start Real-Time Power BI Monitoring
REM This will automatically update Power BI files when facial recognition is used

echo Starting Real-Time Power BI Monitoring...
echo.
echo This script will:
echo 1. Monitor the database for new facial recognition activity
echo 2. Automatically update Power BI export files
echo 3. Allow you to refresh Power BI dashboards instantly
echo.
echo Keep this window open while using the facial recognition system.
echo Press Ctrl+C to stop monitoring.
echo.

cd /d "C:\Users\tec73\STES\STES"
python real_time_powerbi_updater.py

pause 