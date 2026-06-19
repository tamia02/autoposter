# PowerShell setup script: install pip deps and Playwright browsers
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install

Write-Host "Setup complete."
