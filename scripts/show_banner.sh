#!/usr/bin/env bash
# Print Agent4Music ASCII banner (no paths, hostnames, or secrets)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BANNER="${ROOT}/assets/banner.txt"

if [[ -f "$BANNER" ]]; then
  cat "$BANNER"
else
  echo "  Agent4Music — Intelligent Music Data Agent"
fi

echo ""
echo "  Agent4Music | Crawl · Analyze · Visualize"
echo ""
