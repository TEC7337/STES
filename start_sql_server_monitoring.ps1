# SQL Server Integration Monitoring Script
# Continuously runs the SQL Server integration and restarts it if it stops

Write-Host "Starting SQL Server Integration Monitoring..." -ForegroundColor Green
Write-Host "This script will continuously monitor and restart the SQL Server integration if it stops." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the monitoring." -ForegroundColor Red
Write-Host ""

while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] Starting SQL Server integration..." -ForegroundColor Cyan
    
    try {
        # Start the SQL Server integration script
        python sql_server_integration.py
    }
    catch {
        Write-Host "[$timestamp] Error running SQL Server integration: $_" -ForegroundColor Red
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] SQL Server integration stopped. Restarting in 5 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}


