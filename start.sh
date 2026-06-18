#!/bin/bash
set -e
cd "$(dirname "$0")"

PORT="${PORT:-8120}"

bash scripts/show_banner.sh

if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

if command -v npm >/dev/null 2>&1; then
  echo "Building WebUI..."
  (cd webui && npm install --silent && npm run build)
  echo "WebUI ready."
else
  echo "WARN: npm not found. WebUI not built — only /docs available."
  echo "      Run: cd webui && npm install && npm run build"
fi

echo ""
echo "============================================"
echo "  WebUI:     http://127.0.0.1:${PORT}/"
echo "  API Docs:  http://127.0.0.1:${PORT}/docs"
echo "============================================"
echo ""

uvicorn api.main_api:app --host 0.0.0.0 --port "${PORT}" --reload
