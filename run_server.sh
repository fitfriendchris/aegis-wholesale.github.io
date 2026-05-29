#!/usr/bin/env bash
# Aegis Capital — One-click start script
# Starts the Flask API server and opens the dashboard in your default browser

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

echo "🏛️  Aegis Capital Wholesale System"
echo "=================================="
echo ""

# Check if server is already running
if curl -s http://localhost:5001/api/properties > /dev/null 2>&1; then
    echo "✅ API server already running on http://localhost:5001"
else
    echo "🚀 Starting API server..."
    nohup python3 api_server.py > server.log 2>&1 &
    sleep 2
    if curl -s http://localhost:5001/api/properties > /dev/null 2>&1; then
        echo "✅ API server started on http://localhost:5001"
    else
        echo "❌ API server failed to start. Check backend/server.log"
        exit 1
    fi
fi

echo ""
echo "📊 Pipeline:"
curl -s http://localhost:5001/api/pipeline/summary | python3 -m json.tool 2>/dev/null || true

echo ""
echo "🌐 Opening dashboard..."
open "$SCRIPT_DIR/kpi-dashboard.html"

echo ""
echo "=================================="
echo "Done. Dashboard loaded."
