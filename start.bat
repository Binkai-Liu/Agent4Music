@echo off
cd /d %~dp0

type assets\banner.txt 2>nul
echo.
echo   Agent4Music ^| Crawl · Analyze · Visualize
echo.

if not exist venv (
  python -m venv venv
)
call venv\Scripts\activate
pip install -q -r requirements.txt

set PORT=8120
echo.
echo ============================================
echo   WebUI:     http://127.0.0.1:%PORT%/
echo   API Docs:  http://127.0.0.1:%PORT%/docs
echo ============================================
echo.

uvicorn api.main_api:app --host 0.0.0.0 --port %PORT% --reload
