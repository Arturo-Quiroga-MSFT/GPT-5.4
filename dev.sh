#!/usr/bin/env zsh
# dev.sh — Start FastAPI + React dev servers for the stock analysis UI
#
# Usage:
#   ./dev.sh          start both servers (kills anything on ports 8000 / 5173 first)
#   ./dev.sh stop     kill both servers and exit
#   ./dev.sh status   show whether the servers are running
#
# Log files:
#   logs/api.log      FastAPI (uvicorn) output
#   logs/ui.log       Vite dev server output
#
# PID files:
#   .pids/api.pid
#   .pids/ui.pid

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$REPO_ROOT/.venv/bin"
API_DIR="$REPO_ROOT/stock_api"
UI_DIR="$REPO_ROOT/stock_ui"
LOG_DIR="$REPO_ROOT/logs"
PID_DIR="$REPO_ROOT/.pids"
API_PORT=8000
UI_PORT=5173

# ── Colour helpers ────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
RESET='\033[0m'

info()    { print -P "%F{cyan}[dev]%f $*"; }
success() { print -P "%F{green}[dev]%f $*"; }
warn()    { print -P "%F{yellow}[dev]%f $*"; }
error()   { print -P "%F{red}[dev]%f $*"; }

# ── Kill a port (any process listening on it) ─────────────────────────
kill_port() {
  local port=$1
  local pids
  pids=$(lsof -ti tcp:"$port" 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    warn "Killing process(es) on port $port: $pids"
    echo "$pids" | xargs kill -9 2>/dev/null || true
    sleep 0.4
  fi
}

# ── Kill a PID file ───────────────────────────────────────────────────
kill_pid_file() {
  local pid_file=$1
  if [[ -f "$pid_file" ]]; then
    local pid
    pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
      warn "Killing PID $pid (from $pid_file)"
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$pid_file"
  fi
}

# ── Stop both servers ─────────────────────────────────────────────────
stop_all() {
  info "Stopping servers…"
  kill_pid_file "$PID_DIR/api.pid"
  kill_pid_file "$PID_DIR/ui.pid"
  # Belt-and-suspenders: also clear the ports by PID
  kill_port "$API_PORT"
  kill_port "$UI_PORT"
  success "All servers stopped."
}

# ── Status ────────────────────────────────────────────────────────────
show_status() {
  for name in api ui; do
    local pid_file="$PID_DIR/${name}.pid"
    if [[ -f "$pid_file" ]]; then
      local pid
      pid=$(cat "$pid_file")
      if kill -0 "$pid" 2>/dev/null; then
        success "$name  running  (PID $pid)"
      else
        warn "$name  stale PID $pid (process not found) — removing"
        rm -f "$pid_file"
      fi
    else
      warn "$name  not running"
    fi
  done
}

# ── Dispatch subcommands ──────────────────────────────────────────────
case "${1:-start}" in
  stop)   stop_all;    exit 0 ;;
  status) show_status; exit 0 ;;
  start)  ;;  # fall through
  *)
    error "Unknown command '${1}'. Usage: $0 [start|stop|status]"
    exit 1
    ;;
esac

# ── Pre-flight checks ─────────────────────────────────────────────────
if [[ ! -x "$VENV/python" ]]; then
  error "Python venv not found at $VENV — run: python -m venv .venv && pip install -r requirements.txt"
  exit 1
fi

if [[ ! -f "$UI_DIR/package.json" ]]; then
  error "stock_ui/package.json not found — is the repo fully cloned?"
  exit 1
fi

if ! command -v node &>/dev/null; then
  error "Node.js not found on PATH"
  exit 1
fi

# ── Create directories ────────────────────────────────────────────────
mkdir -p "$LOG_DIR" "$PID_DIR"

# ── Stop any previous instances ───────────────────────────────────────
info "Clearing any previous instances on ports $API_PORT and $UI_PORT…"
kill_pid_file "$PID_DIR/api.pid"
kill_pid_file "$PID_DIR/ui.pid"
kill_port "$API_PORT"
kill_port "$UI_PORT"

# ── Install UI deps if node_modules is missing ────────────────────────
if [[ ! -d "$UI_DIR/node_modules" ]]; then
  info "node_modules not found — running npm install…"
  (cd "$UI_DIR" && npm install --silent)
fi

# ── Start FastAPI ─────────────────────────────────────────────────────
info "Starting FastAPI on port $API_PORT…"
(
  cd "$API_DIR"
  "$VENV/uvicorn" main:app --reload --port "$API_PORT" \
    >> "$LOG_DIR/api.log" 2>&1 &
  echo $! > "$PID_DIR/api.pid"
)

# ── Wait for FastAPI to be ready (up to 15 s) ────────────────────────
info "Waiting for FastAPI to be ready…"
for i in {1..30}; do
  if curl -sf "http://localhost:$API_PORT/api/health" &>/dev/null; then
    success "FastAPI ready  →  http://localhost:$API_PORT"
    break
  fi
  if [[ $i -eq 30 ]]; then
    error "FastAPI did not become ready in time. Check logs/api.log"
    cat "$LOG_DIR/api.log" | tail -20
    stop_all
    exit 1
  fi
  sleep 0.5
done

# ── Start Vite ────────────────────────────────────────────────────────
info "Starting Vite dev server on port $UI_PORT…"
(
  cd "$UI_DIR"
  npm run dev -- --port "$UI_PORT" \
    >> "$LOG_DIR/ui.log" 2>&1 &
  echo $! > "$PID_DIR/ui.pid"
)

# ── Wait for Vite to be ready (up to 15 s) ───────────────────────────
info "Waiting for Vite to be ready…"
for i in {1..30}; do
  if curl -sf "http://localhost:$UI_PORT" &>/dev/null; then
    success "Vite ready      →  http://localhost:$UI_PORT"
    break
  fi
  if [[ $i -eq 30 ]]; then
    error "Vite did not become ready in time. Check logs/ui.log"
    cat "$LOG_DIR/ui.log" | tail -20
    stop_all
    exit 1
  fi
  sleep 0.5
done

# ── Summary ───────────────────────────────────────────────────────────
echo ""
success "Both servers are running."
print -P "  %F{cyan}API%f   http://localhost:$API_PORT   (logs/api.log)"
print -P "  %F{cyan}UI%f    http://localhost:$UI_PORT   (logs/ui.log)"
echo ""
print -P "  %F{yellow}./dev.sh stop%f    — stop both servers"
print -P "  %F{yellow}./dev.sh status%f  — check if running"
echo ""
