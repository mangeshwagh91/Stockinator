# Install pymongo and motor if not already installed
Write-Host "Installing MongoDB packages..." -ForegroundColor Cyan
pip install pymongo==4.6.1 motor==3.3.2 --quiet

Write-Host "`nChecking installation..." -ForegroundColor Cyan
python -c "import pymongo; import motor; print(f'✓ pymongo {pymongo.__version__}'); print(f'✓ motor {motor.version}')"

Write-Host "`nStarting historical data download..." -ForegroundColor Green
Write-Host "This will download 30 years of data for 50 major Indian stocks" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to cancel at any time`n" -ForegroundColor Yellow

# Run the download script
python scripts/download_historical_data.py
