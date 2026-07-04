#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/logs"

BACKEND_PORT="${DEEPANALYZE_BACKEND_PORT:-${BACKEND_PORT:-8200}}"
FRONTEND_PORT="${FRONTEND_PORT:-4000}"
FILE_SERVER_PORT="${DEEPANALYZE_FILE_SERVER_PORT:-${FILE_SERVER_PORT:-8100}}"
BACKEND_HOST="${DEEPANALYZE_BACKEND_HOST:-0.0.0.0}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
USE_WASM_SWC="${USE_WASM_SWC:-auto}"

mkdir -p "$LOG_DIR"

python_can_run_backend() {
    "$1" - <<'PY' >/dev/null 2>&1
import uvicorn
import fastapi
PY
}

select_python_bin() {
    local current_python
    current_python="$(command -v python 2>/dev/null || true)"
    if [ -n "$current_python" ] && python_can_run_backend "$current_python"; then
        printf "%s\n" "$current_python"
        return
    fi

    if command -v conda >/dev/null 2>&1; then
        local conda_python
        conda_python="$(conda run -n deepanalyze_app python -c 'import sys; print(sys.executable)' 2>/dev/null | tail -n 1 || true)"
        if [ -n "$conda_python" ] && python_can_run_backend "$conda_python"; then
            printf "%s\n" "$conda_python"
            return
        fi
    fi

    printf "%s\n" "${current_python:-python}"
}

PYTHON_BIN="${PYTHON_BIN:-$(select_python_bin)}"

echo "Starting DeepAnalyze WebUI v2"
echo "============================="
echo "Project:  $ROOT_DIR"
echo "Backend:  http://localhost:$BACKEND_PORT"
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Python:   $PYTHON_BIN"
echo ""

kill_pid_file() {
    local name="$1"
    local pid_file="$2"

    if [ ! -f "$pid_file" ]; then
        return
    fi

    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "Stopping old $name process: $pid"
        kill "$pid" 2>/dev/null || true
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    fi
    rm -f "$pid_file"
}

release_port() {
    local port="$1"
    local pids
    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [ -z "$pids" ]; then
        return
    fi

    echo "Releasing port $port: $pids"
    kill $pids 2>/dev/null || true
    sleep 1
    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [ -n "$pids" ]; then
        kill -9 $pids 2>/dev/null || true
    fi
}

wait_for_http() {
    local name="$1"
    local url="$2"
    local timeout_sec="$3"
    local log_file="$4"
    local elapsed=0

    while [ "$elapsed" -lt "$timeout_sec" ]; do
        if curl -fsS -I "$url" >/dev/null 2>&1 || curl -fsS "$url" >/dev/null 2>&1; then
            echo "$name is ready: $url"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done

    echo ""
    echo "ERROR: $name did not become ready within ${timeout_sec}s: $url"
    echo "Last log lines from $log_file:"
    tail -80 "$log_file" 2>/dev/null || true
    return 1
}

frontend_needs_wasm_swc() {
    if [ "$USE_WASM_SWC" = "1" ] || [ "$USE_WASM_SWC" = "true" ]; then
        return 0
    fi
    if [ "$USE_WASM_SWC" = "0" ] || [ "$USE_WASM_SWC" = "false" ]; then
        return 1
    fi

    local node_major
    node_major="$(node -p "Number.parseInt(process.versions.node.split('.')[0], 10)" 2>/dev/null || true)"
    if [ -n "$node_major" ] && [ "$node_major" -ge 23 ] 2>/dev/null; then
        return 0
    fi

    if (
        cd "$FRONTEND_DIR"
        node - <<'JS' >/dev/null 2>&1
try {
  require("./node_modules/@next/swc-linux-x64-gnu/next-swc.linux-x64-gnu.node")
  process.exit(0)
} catch (_) {
  process.exit(1)
}
JS
    ); then
        return 1
    fi

    return 0
}

ensure_frontend_dependencies() {
    if [ ! -d "$FRONTEND_DIR/node_modules" ] || [ ! -f "$FRONTEND_DIR/node_modules/next/dist/bin/next" ]; then
        echo "Frontend dependencies are missing."
        echo "Run this once:"
        echo "  cd $FRONTEND_DIR && npm install"
        exit 1
    fi
}

ensure_wasm_swc() {
    local next_version
    next_version="$(cd "$FRONTEND_DIR" && node -p "require('./node_modules/next/package.json').version")"

    if [ ! -f "$FRONTEND_DIR/node_modules/@next/swc-wasm-nodejs/wasm.js" ]; then
        echo "Installing @next/swc-wasm-nodejs@$next_version for this host..."
        (cd "$FRONTEND_DIR" && npm install --no-save "@next/swc-wasm-nodejs@$next_version")
    fi
}

echo "Cleaning old WebUI processes..."
kill_pid_file "backend" "$LOG_DIR/backend.pid"
kill_pid_file "frontend" "$LOG_DIR/frontend.pid"
pkill -f "python.*backend.py" 2>/dev/null || true
pkill -f "npm.*next dev" 2>/dev/null || true
pkill -f "node_modules/next/dist/bin/next dev" 2>/dev/null || true
release_port "$BACKEND_PORT"
release_port "$FRONTEND_PORT"
echo ""

echo "Starting backend..."
: > "$LOG_DIR/backend.log"
nohup setsid bash -c 'cd "$1" || exit 1; shift; exec "$@"' bash "$ROOT_DIR" \
    env \
    "PYTHONPATH=$ROOT_DIR:${PYTHONPATH:-}" \
    "DEEPANALYZE_BACKEND_HOST=$BACKEND_HOST" \
    "DEEPANALYZE_BACKEND_PORT=$BACKEND_PORT" \
    "DEEPANALYZE_FILE_SERVER_PORT=$FILE_SERVER_PORT" \
    "$PYTHON_BIN" backend.py \
    > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"
echo "Backend PID: $BACKEND_PID"
wait_for_http "Backend" "http://127.0.0.1:$BACKEND_PORT/docs" 60 "$LOG_DIR/backend.log"
echo ""

ensure_frontend_dependencies

echo "Starting frontend..."
: > "$LOG_DIR/frontend.log"
if frontend_needs_wasm_swc; then
    ensure_wasm_swc
    echo "Using Next.js WASM SWC fallback for frontend startup."
    nohup setsid bash -c 'cd "$1" || exit 1; shift; exec "$@"' bash "$FRONTEND_DIR" \
        env \
        "NEXT_PUBLIC_BACKEND_URL=http://localhost:$BACKEND_PORT" \
        "NEXT_TEST_WASM=1" \
        "NEXT_TEST_WASM_DIR=$FRONTEND_DIR/node_modules/@next/swc-wasm-nodejs" \
        npx -y node@22.12.0 node_modules/next/dist/bin/next dev --webpack -H "$FRONTEND_HOST" -p "$FRONTEND_PORT" \
        > "$LOG_DIR/frontend.log" 2>&1 &
else
    nohup setsid bash -c 'cd "$1" || exit 1; shift; exec "$@"' bash "$FRONTEND_DIR" \
        env \
        "NEXT_PUBLIC_BACKEND_URL=http://localhost:$BACKEND_PORT" \
        npm run dev -- -H "$FRONTEND_HOST" -p "$FRONTEND_PORT" \
        > "$LOG_DIR/frontend.log" 2>&1 &
fi
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$LOG_DIR/frontend.pid"
echo "Frontend PID: $FRONTEND_PID"
wait_for_http "Frontend" "http://127.0.0.1:$FRONTEND_PORT" 120 "$LOG_DIR/frontend.log"

echo ""
echo "All services started successfully."
echo ""
echo "Service URLs:"
echo "  WebUI frontend: http://localhost:$FRONTEND_PORT"
echo "  WebUI backend:  http://localhost:$BACKEND_PORT"
echo "  Model API:      http://localhost:8000/v1  (start separately)"
echo ""
echo "For Cursor/SSH remote use, forward these ports:"
echo "  $FRONTEND_PORT and $BACKEND_PORT"
echo ""
echo "Log files:"
echo "  Backend:  $LOG_DIR/backend.log"
echo "  Frontend: $LOG_DIR/frontend.log"
echo ""
echo "Stop services: bash stop.sh"
