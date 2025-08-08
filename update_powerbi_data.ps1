# Auto-Updating Power BI Export PowerShell Script
# Run this with Windows Task Scheduler for automatic updates

Write-Host "Starting Power BI data update..." -ForegroundColor Green

# Change to the STES directory
Set-Location "C:\Users\tec73\STES\STES"

# Run the Python script
python auto_update_powerbi_exports.py

Write-Host "Power BI data update completed." -ForegroundColor Green 