#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/zZedix/Shifter.git"
TARGET_DIR="${TARGET_DIR:-$HOME/Shifter}"
PID_FILE="${TARGET_DIR}/shifter-webui.pid"
LOG_FILE="${TARGET_DIR}/shifter-webui.log"

log() {
    printf '[Shifter Toolkit installer] %s\n' "$*"
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log "Missing dependency: $1"
        log "Please install '$1' with your package manager and re-run this script."
        exit 1
    fi
}

require_command git
require_command python3
require_command pip3

if [[ -d "${TARGET_DIR}/.git" ]]; then
    log "Repository already present at ${TARGET_DIR}. Pulling latest changes..."
    git -C "${TARGET_DIR}" pull --ff-only
else
    log "Cloning Shifter Toolkit into ${TARGET_DIR}..."
    git clone "${REPO_URL}" "${TARGET_DIR}"
fi

log "Installing Python dependencies..."
python3 -m pip install --upgrade pip setuptools wheel

log "Installing Shifter Toolkit in editable mode..."
python3 -m pip install -e "${TARGET_DIR}"

cleanup_stale_pid() {
    if [[ -f "${PID_FILE}" ]]; then
        local old_pid
        old_pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
        if [[ -n "${old_pid}" ]] && ! kill -0 "${old_pid}" 2>/dev/null; then
            rm -f "${PID_FILE}"
        fi
    fi
}

start_daemon() {
    if ! command -v shifter-toolkit >/dev/null 2>&1; then
        log "Cannot locate 'shifter-toolkit' in PATH. Skipping background start."
        return 1
    fi

    cleanup_stale_pid

    if [[ -f "${PID_FILE}" ]]; then
        local running_pid
        running_pid="$(cat "${PID_FILE}")"
        if kill -0 "${running_pid}" 2>/dev/null; then
            log "WebUI already running (PID ${running_pid}). Logs: ${LOG_FILE}"
            return 0
        fi
    fi

    log "Starting WebUI daemon (logs: ${LOG_FILE})..."
    nohup shifter-toolkit serve --host 0.0.0.0 --port 2063 >"${LOG_FILE}" 2>&1 &
    local new_pid=$!
    sleep 1
    if kill -0 "${new_pid}" 2>/dev/null; then
        echo "${new_pid}" > "${PID_FILE}"
        log "WebUI started in background with PID ${new_pid}."
    else
        log "Failed to start WebUI daemon. Check ${LOG_FILE} for details."
        return 1
    fi
}

if [[ "$(id -u)" -eq 0 ]]; then
    start_daemon || true
else
    log "Run this script with sudo/root if you want the WebUI to start as a daemon automatically."
    log "You can manually launch it with:"
    echo "  sudo shifter-toolkit serve --host 0.0.0.0 --port 2063 &> ${LOG_FILE} &"
fi

cat <<EOF

Installation complete!

To run the Web UI manually:
  sudo shifter-toolkit serve --host 0.0.0.0 --port 2063

To open the CLI help:
  shifter-toolkit --help

Background service PID file:
  ${PID_FILE}
Log file:
  ${LOG_FILE}

Project directory: ${TARGET_DIR}
EOF
