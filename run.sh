#!/usr/bin/env bash
# run.sh — Launch ubuntu-storage-analyzer in the background.
# Logs go to ~/.config/ubuntu-storage-analyzer/app.log
# PID is written to ~/.config/ubuntu-storage-analyzer/app.pid

set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/.config/ubuntu-storage-analyzer"
PID_FILE="$LOG_DIR/app.pid"
LOG_FILE="$LOG_DIR/app.log"

mkdir -p "$LOG_DIR"

# ── Already running? ──────────────────────────────────────────────────────────
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Already running (PID $OLD_PID). Use './run.sh stop' to stop it."
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# ── Sub-commands ──────────────────────────────────────────────────────────────
CMD="${1:-start}"

case "$CMD" in

  start)
    if [[ ! -d "$APP_DIR/venv" ]]; then
        echo "Virtual environment not found. Running setup first…"
        bash "$APP_DIR/setup.sh"
    fi

    echo "Starting Ubuntu Storage Analyzer in background…"
    nohup "$APP_DIR/venv/bin/python" "$APP_DIR/main.py" \
        >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Started (PID $(cat "$PID_FILE"))."
    echo "Logs: $LOG_FILE"
    ;;

  stop)
    if [[ ! -f "$PID_FILE" ]]; then
        echo "Not running (no PID file found)."
        exit 0
    fi
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID"
        rm -f "$PID_FILE"
        echo "Stopped (PID $PID)."
    else
        echo "Process $PID not found (already stopped)."
        rm -f "$PID_FILE"
    fi
    ;;

  restart)
    "$0" stop
    sleep 1
    "$0" start
    ;;

  status)
    if [[ -f "$PID_FILE" ]]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Running (PID $PID)."
        else
            echo "Not running (stale PID file)."
            rm -f "$PID_FILE"
        fi
    else
        echo "Not running."
    fi
    ;;

  log)
    tail -f "$LOG_FILE"
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status|log}"
    exit 1
    ;;
esac
