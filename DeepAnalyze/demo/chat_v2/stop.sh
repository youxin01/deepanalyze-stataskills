#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
BACKEND_PORT="${DEEPANALYZE_BACKEND_PORT:-${BACKEND_PORT:-8200}}"
FRONTEND_PORT="${FRONTEND_PORT:-4000}"

cd "$ROOT_DIR"

echo "Stopping DeepAnalyze WebUI v2"
echo "============================="

# Stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            sleep 1
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "   Force stopping $service_name..."
                kill -9 "$pid" 2>/dev/null || true
            fi
            echo "   $service_name stopped."
        else
            echo "   $service_name process not found."
        fi
        rm -f "$pid_file"
    else
        echo "   PID file for $service_name not found."
    fi
}

# Stop services
stop_service "Backend API" "$LOG_DIR/backend.pid"
stop_service "Next.js Frontend" "$LOG_DIR/frontend.pid"

echo ""
echo "Cleaning up remaining processes..."

# Kill by process name (just in case)
pkill -f "python.*backend.py" 2>/dev/null && echo "   Cleaned up backend.py process." || true
pkill -f "npm.*next dev" 2>/dev/null && echo "   Cleaned up npm next dev process." || true
pkill -f "node_modules/next/dist/bin/next dev" 2>/dev/null && echo "   Cleaned up next dev process." || true
pkill -f "next.*dev" 2>/dev/null && echo "   Cleaned up remaining next dev process." || true
pkill -f "next-server" 2>/dev/null && echo "   Cleaned up next-server process." || true
pkill -f "next/dist/telemetry/detached-flush.js" 2>/dev/null && echo "   Cleaned up Next.js telemetry flush process." || true

echo ""
echo "Releasing ports..."

# WebUI v2 starts only the backend and frontend ports. Workspace file APIs are
# served by the backend; there is no separate 8100 process in this demo.
for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
    # Only kill TCP LISTENers
    pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "   Releasing port $port (PIDs: $pids)..."
        kill $pids 2>/dev/null || true
        sleep 1
        pids2=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
        if [ -n "$pids2" ]; then
            echo "   Force releasing port $port (PIDs: $pids2)..."
            kill -9 $pids2 2>/dev/null || true
        fi
    fi
done

echo ""
echo "Checking for remaining processes..."
remaining_processes="$(ps aux | grep -E "(backend\.py|npm.*next dev|node_modules/next/dist/bin/next dev|next.*dev|next-server|next/dist/telemetry/detached-flush\.js)" | grep -v grep || true)"
remaining=$(printf "%s\n" "$remaining_processes" | sed '/^[[:space:]]*$/d' | wc -l)
if [ "$remaining" -eq 0 ]; then
    echo "   All processes have been stopped."
else
    echo "   Warning: $remaining related processes are still running:"
    printf "%s\n" "$remaining_processes"
fi

echo ""
echo "System stopped successfully."
echo ""
echo "Log files are kept in the logs/ directory."
echo "To restart the system: bash start.sh"
