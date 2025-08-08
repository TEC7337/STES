@echo off
REM Auto-Updating Power BI Export Batch File
REM Run this with Windows Task Scheduler for automatic updates

echo Starting Power BI data update...
cd /d "C:\Users\tec73\STES\STES"
python auto_update_powerbi_exports.py
echo Power BI data update completed.
pause 