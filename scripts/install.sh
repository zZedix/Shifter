#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/zZedix/Shifter.git"
TARGET_DIR="${TARGET_DIR:-$HOME/Shifter}"
PID_FILE="${TARGET_DIR}/shifter-webui.pid"
LOG_FILE="${TARGET_DIR}/shifter-webui.log"
APT_UPDATED=0
PACMAN_SYNCED=0

log() {
    printf '[Shifter Toolkit installer] %s\n' "$*"
}

error() {
    printf '[Shifter Toolkit installer] ERROR: %s\n' "$*" >&2
}

require_command() {
    local cmd="$1"
    local pkg_apt="${2:-$cmd}"
    local pkg_dnf="${3:-$pkg_apt}"
    local pkg_pacman="${4:-$pkg_apt}"

    if command -v "${cmd}" >/dev/null 2>&1; then
        return 0
    fi

    if [[ "$(id -u)" -ne 0 ]]; then
        error "Missing dependency '${cmd}'. Re-run this script with sudo/root so it can install '${pkg_apt}'."
        exit 1
    fi

    if command -v apt-get >/dev/null 2>&1; then
        if [[ "${APT_UPDATED}" -eq 0 ]]; then
            log "Updating apt package index..."
            apt-get update -y
            APT_UPDATED=1
        fi
        log "Installing '${pkg_apt}' via apt-get..."
        apt-get install -y "${pkg_apt}"
    elif command -v dnf >/dev/null 2>&1; then
        log "Installing '${pkg_dnf}' via dnf..."
        dnf install -y "${pkg_dnf}"
    elif command -v yum >/dev/null 2>&1; then
        log "Installing '${pkg_dnf}' via yum..."
        yum install -y "${pkg_dnf}"
    elif command -v pacman >/dev/null 2>&1; then
        if [[ "${PACMAN_SYNCED}" -eq 0 ]]; then
            log "Syncing pacman package databases..."
            pacman -Sy --noconfirm
            PACMAN_SYNCED=1
        fi
        log "Installing '${pkg_pacman}' via pacman..."
        pacman -S --noconfirm "${pkg_pacman}"
    else
        error "Unsupported package manager. Please install '${pkg_apt}' manually and re-run the installer."
        exit 1
    fi

    if ! command -v "${cmd}" >/dev/null 2>&1; then
        error "Failed to install '${cmd}'. Please install it manually and retry."
        exit 1
    fi
}

require_command git git git git
require_command python3 python3 python3 python
require_command pip3 python3-pip python3-pip python-pip

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
