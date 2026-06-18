#!/bin/bash
set -e
cd "$(dirname "$0")"

PORT="${PORT:-8120}"
SKIP_WEBUI="${SKIP_WEBUI_BUILD:-0}"

bash scripts/show_banner.sh

echo "[1/4] Preparing Python environment..."
if [ ! -d "venv" ]; then
  echo "      Creating venv..."
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate

echo "[2/4] Installing Python dependencies (first run may take 1-3 min)..."
pip install -r requirements.txt

if [ "$SKIP_WEBUI" = "1" ]; then
  echo "[3/4] Skipping WebUI build (SKIP_WEBUI_BUILD=1)."
elif [ -f "webui/dist/index.html" ] && [ "$SKIP_WEBUI" != "force" ]; then
  echo "[3/4] WebUI already built (webui/dist/). Skipping. Set SKIP_WEBUI_BUILD=force to rebuild."
elif command -v npm >/dev/null 2>&1 || command -v /usr/bin/npm >/dev/null 2>&1; then
  NPM=$(command -v npm 2>/dev/null || echo /usr/bin/npm)
  echo "[3/4] Building WebUI (npm install + build, may take 2-5 min)..."
  (cd webui && "$NPM" install && "$NPM" run build)
  echo "      WebUI ready."
else
  echo "[3/4] ERROR: npm not found — WebUI was NOT built."
  echo "      Install Node.js, then rebuild:"
  echo "        sudo apt-get install -y nodejs npm    # Debian/Ubuntu"
  echo "        cd webui && npm install && npm run build"
  echo "      Without WebUI, only http://127.0.0.1:${PORT}/docs works."
fi

echo ""
if [ -f "webui/dist/index.html" ]; then
  echo "============================================"
  echo "  WebUI:     http://127.0.0.1:${PORT}/"
  echo "  API Docs:  http://127.0.0.1:${PORT}/docs"
  echo "============================================"
else
  echo "============================================"
  echo "  API Docs:  http://127.0.0.1:${PORT}/docs"
  echo "  WebUI:     NOT BUILT (see [3/4] above)"
  echo "============================================"
fi
echo ""
echo "[4/4] Starting API server..."
echo ""

uvicorn api.main_api:app --host 0.0.0.0 --port "${PORT}" --reload
