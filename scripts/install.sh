#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/zZedix/Shifter.git"
TARGET_DIR="${TARGET_DIR:-$HOME/Shifter}"
PID_FILE="${TARGET_DIR}/shifter-webui.pid"
LOG_FILE="${TARGET_DIR}/shifter-webui.log"
BASE_PATH_FILE="${TARGET_DIR}/shifter-webui.basepath"
BASE_PATH=""
APT_UPDATED=0
PACMAN_SYNCED=0

log() {
    printf '[Shifter Toolkit installer] %s\n' "$*"
}

error() {
    printf '[Shifter Toolkit installer] ERROR: %s\n' "$*" >&2
}

generate_base_path() {
    local input="${WEBUI_BASE_PATH:-}"
    if [[ -n "${input}" ]]; then
        printf '%s\n' "${input}"
        return
    fi
    python3 - <<'PY'
import secrets
import string

alphabet = string.ascii_letters + string.digits
print(''.join(secrets.choice(alphabet) for _ in range(12)))
PY
}

normalize_base_path() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    if [[ -z "${value//[[:space:]]/}" ]]; then
        printf '/\n'
        return
    fi
    if [[ -z "${value}" ]]; then
        printf '/\n'
        return
    fi
    [[ "${value}" != /* ]] && value="/${value}"
    [[ "${value}" != '/' ]] && value="/${value#/}"
    [[ "${value}" != '/' ]] && value="${value%/}"
    printf '%s\n' "${value}"
}

load_base_path() {
    if [[ -f "${BASE_PATH_FILE}" ]]; then
        BASE_PATH="$(cat "${BASE_PATH_FILE}")"
    fi
    if [[ -z "${BASE_PATH}" ]]; then
        BASE_PATH="/$(generate_base_path)"
    fi
    BASE_PATH="$(normalize_base_path "${BASE_PATH}")"
    if [[ -d "$(dirname "${BASE_PATH_FILE}")" ]]; then
        printf '%s\n' "${BASE_PATH}" > "${BASE_PATH_FILE}"
    fi
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

ensure_pip() {
    if python3 -m pip --version >/dev/null 2>&1; then
        return 0
    fi

    if [[ "$(id -u)" -ne 0 ]]; then
        error "Python's pip module is missing. Re-run with sudo/root so it can be installed automatically."
        exit 1
    fi

    if command -v apt-get >/dev/null 2>&1; then
        if [[ "${APT_UPDATED}" -eq 0 ]]; then
            log "Updating apt package index..."
            apt-get update -y
            APT_UPDATED=1
        fi
        log "Installing python3-pip via apt-get..."
        apt-get install -y python3-pip
    elif command -v dnf >/dev/null 2>&1; then
        log "Installing python3-pip via dnf..."
        dnf install -y python3-pip
    elif command -v yum >/dev/null 2>&1; then
        log "Installing python3-pip via yum..."
        yum install -y python3-pip
    elif command -v pacman >/dev/null 2>&1; then
        if [[ "${PACMAN_SYNCED}" -eq 0 ]]; then
            log "Syncing pacman package databases..."
            pacman -Sy --noconfirm
            PACMAN_SYNCED=1
        fi
        log "Installing python-pip via pacman..."
        pacman -S --noconfirm python-pip
    fi

    if ! python3 -m pip --version >/dev/null 2>&1; then
        log "Attempting to bootstrap pip using python3 -m ensurepip..."
        python3 -m ensurepip --upgrade >/dev/null 2>&1 || true
    fi

    if ! python3 -m pip --version >/dev/null 2>&1; then
        error "Unable to install Python pip. Please install it manually and re-run the installer."
        exit 1
    fi
}

ensure_pip

load_base_path
log "Using WebUI base path: ${BASE_PATH}"

if [[ -d "${TARGET_DIR}/.git" ]]; then
    log "Repository already present at ${TARGET_DIR}. Pulling latest changes..."
    git -C "${TARGET_DIR}" pull --ff-only
else
    log "Cloning Shifter Toolkit into ${TARGET_DIR}..."
    git clone "${REPO_URL}" "${TARGET_DIR}"
fi

printf '%s\n' "${BASE_PATH}" > "${BASE_PATH_FILE}"

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
            log "WebUI already running (PID ${running_pid}) at path '${BASE_PATH}'. Logs: ${LOG_FILE}"
            return 0
        fi
    fi

    log "Starting WebUI daemon at path '${BASE_PATH}' (logs: ${LOG_FILE})..."
    nohup shifter-toolkit serve --host 0.0.0.0 --port 2063 --base-path "${BASE_PATH}" >"${LOG_FILE}" 2>&1 &
    local new_pid=$!
    sleep 1
    if kill -0 "${new_pid}" 2>/dev/null; then
        echo "${new_pid}" > "${PID_FILE}"
        log "WebUI started in background with PID ${new_pid}."
        log "Visit: http://$(hostname -f 2>/dev/null || echo localhost):2063${BASE_PATH}"
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
    echo "  sudo shifter-toolkit serve --host 0.0.0.0 --port 2063 --base-path '${BASE_PATH}' &> ${LOG_FILE} &"
fi

HOST_HINT="$(hostname -f 2>/dev/null || echo localhost)"

cat <<EOF

Installation complete!

To run the Web UI manually:
  sudo shifter-toolkit serve --host 0.0.0.0 --port 2063 --base-path '${BASE_PATH}'

To open the CLI help:
  shifter-toolkit --help

Background service PID file:
  ${PID_FILE}
Log file:
  ${LOG_FILE}

Project directory: ${TARGET_DIR}
Web UI path: ${BASE_PATH}
Endpoint example:
  http://${HOST_HINT}:2063${BASE_PATH}
Base path record:
  ${BASE_PATH_FILE}
EOF
