#!/usr/bin/env bash
set -euo pipefail

# shifter-installer-branch: main

# Default branch to install from GitHub.
# Git branch to install; override via WEBUI_BRANCH if needed.
DEFAULT_BRANCH="${WEBUI_BRANCH:-main}"
REPO_URL="https://github.com/zZedix/Shifter.git"
TARGET_DIR="${TARGET_DIR:-$HOME/Shifter}"
PID_FILE="${TARGET_DIR}/shifter-webui.pid"
LOG_FILE="${TARGET_DIR}/shifter-webui.log"
BASE_PATH_FILE="${TARGET_DIR}/shifter-webui.basepath"
VERSION_FILE="${TARGET_DIR}/shifter-version.txt"
CONFIG_DIR="${TARGET_DIR}/config"
AUTH_FILE="${CONFIG_DIR}/auth.json"
BASE_PATH=""
APT_UPDATED=0
PACMAN_SYNCED=0
GENERATED_USERNAME=""
GENERATED_PASSWORD=""
CERTBOT_ENABLED=0
CERT_DOMAIN=""
CERT_EMAIL=""
CERT_FULLCHAIN=""
CERT_PRIVKEY=""
INSTALLER_TTY=""
if [[ -e /dev/tty && -r /dev/tty && -w /dev/tty ]]; then
    INSTALLER_TTY="/dev/tty"
fi

if [[ -n "${INSTALLER_TTY}" ]]; then
    INSTALLER_INTERACTIVE=1
else
    INSTALLER_INTERACTIVE=0
fi
NONINTERACTIVE_MSG_PRINTED=0

random_alnum() {
    local length="${1:-16}"
    LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c "${length}"
}

write_auth_json() {
    local username="$1"
    local password_hash="$2"
    mkdir -p "$(dirname "${AUTH_FILE}")"
    cat >"${AUTH_FILE}" <<EOF
{
    "username": "${username}",
    "password_hash": "${password_hash}",
    "cert_paths": {}
}
EOF
    chmod 600 "${AUTH_FILE}" 2>/dev/null || true
}

fallback_generate_credentials() {
    if ! command -v shifter-toolkit >/dev/null 2>&1; then
        return 1
    fi

    local username="shifter-$(random_alnum 6)"
    local placeholder_hash='$2b$12$Jm5M1HgeoJZ4YR6jliOpze3oFUaVWYZ3RKlxv..q6tDAQjPF1WGB6'
    write_auth_json "${username}" "${placeholder_hash}"

    log "Falling back to shifter-toolkit reset-credentials..."
    local output password
    if ! output="$(SHIFTER_CONFIG_DIR="${CONFIG_DIR}" SHIFTER_AUTH_FILE="${AUTH_FILE}" shifter-toolkit reset-credentials --username "${username}" --generate --length 20 2>&1)"; then
        log "Credential fallback via shifter-toolkit failed:\n${output}"
        return 1
    fi

    password="$(printf '%s\n' "${output}" | awk -F': ' '/Password:/ {print $2}' | tail -n1)"
    if [[ -z "${password}" ]]; then
        log "Credential fallback succeeded but password could not be parsed. Output:\n${output}"
        return 1
    fi

    GENERATED_USERNAME="${username}"
    GENERATED_PASSWORD="${password}"
    log "Credentials generated via fallback."
    return 0
}

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

generate_credentials() {
    if [[ -f "${AUTH_FILE}" ]]; then
        log "Authentication configuration already exists at ${AUTH_FILE}; skipping credential generation."
        return
    fi

    log "Generating secure WebUI credentials..."

    local cli_username="shifter-$(random_alnum 6)"
    local cli_password="$(random_alnum 20)"
    local placeholder_hash='$2b$12$Jm5M1HgeoJZ4YR6jliOpze3oFUaVWYZ3RKlxv..q6tDAQjPF1WGB6'
    write_auth_json "${cli_username}" "${placeholder_hash}"

    if command -v shifter-toolkit >/dev/null 2>&1; then
        local cli_output=""
        if cli_output="$(SHIFTER_CONFIG_DIR="${CONFIG_DIR}" SHIFTER_AUTH_FILE="${AUTH_FILE}" shifter-toolkit reset-credentials --username "${cli_username}" --password "${cli_password}" 2>&1)"; then
            GENERATED_USERNAME="${cli_username}"
            GENERATED_PASSWORD="${cli_password}"
            log "Credentials generated via shifter-toolkit CLI."
            return
        fi
        log "shifter-toolkit reset-credentials failed, falling back to Python:\n${cli_output}"
    fi

    local output=""
    local python_status=0
    local python_cmd=(python3)

    if command -v timeout >/dev/null 2>&1; then
        python_cmd=(timeout 30 python3)
    fi

    output="$(
        CONFIG_DIR="${CONFIG_DIR}" AUTH_FILE="${AUTH_FILE}" PYTHONUNBUFFERED=1 "${python_cmd[@]}" - <<'PY'
import json
import os
import secrets
import string
import sys
import bcrypt
from pathlib import Path

config_dir = Path(os.environ["CONFIG_DIR"])
auth_file = Path(os.environ["AUTH_FILE"])
config_dir.mkdir(parents=True, exist_ok=True)

alphabet = string.ascii_letters + string.digits
username = "shifter-" + "".join(secrets.choice(alphabet) for _ in range(6))
password = "".join(secrets.choice(alphabet) for _ in range(20))
password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

payload = {
    "username": username,
    "password_hash": password_hash,
    "cert_paths": {}
}

with auth_file.open("w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=4)
    handle.write("\n")

try:
    os.chmod(auth_file, 0o600)
except OSError:
    pass

sys.stdout.write(f"USERNAME={username}\nPASSWORD={password}\n")
sys.stdout.flush()
PY
    2>&1)" || python_status=$?

    if [[ ${python_status} -ne 0 || -z "${output}" ]]; then
        log "Python-based credential generation failed or timed out (exit code: ${python_status})."
        if [[ -n "${output}" ]]; then
            log "Python output:\n${output}"
        fi
        if fallback_generate_credentials; then
            return
        fi
        error "Unable to generate credentials automatically. Please run:\n  sudo shifter-toolkit reset-credentials --generate\nand rerun the installer."
        exit 1
    fi

    while IFS='=' read -r key value; do
        case "${key}" in
            USERNAME) GENERATED_USERNAME="${value}" ;;
            PASSWORD) GENERATED_PASSWORD="${value}" ;;
        esac
    done <<<"${output}"
}

update_auth_cert_paths() {
    if [[ -z "${CERT_FULLCHAIN}" || -z "${CERT_PRIVKEY}" ]]; then
        return
    fi

    python3 - <<PY
import json
from pathlib import Path

auth_path = Path(r"""${AUTH_FILE}""")
if not auth_path.exists():
    raise SystemExit("auth.json missing; cannot write certificate paths.")

with auth_path.open("r", encoding="utf-8") as handle:
    data = json.load(handle)

cert_paths = data.setdefault("cert_paths", {})
cert_paths["fullchain"] = r"""${CERT_FULLCHAIN}"""
cert_paths["privkey"] = r"""${CERT_PRIVKEY}"""

auth_path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")
PY
}

maybe_configure_https() {
    local answer choice
    CERTBOT_ENABLED=0
    CERT_DOMAIN=""
    CERT_EMAIL=""
    CERT_FULLCHAIN=""
    CERT_PRIVKEY=""

    if [[ -n "${SHIFTER_ENABLE_HTTPS:-}" ]]; then
        answer="${SHIFTER_ENABLE_HTTPS}"
    elif [[ "${INSTALLER_INTERACTIVE}" -eq 1 ]]; then
        if ! read -r -p "Do you want to run with a domain (HTTPS)? [y/N] " answer <"${INSTALLER_TTY}" 2>/dev/null; then
            answer=""
        fi
    else
        if [[ "${NONINTERACTIVE_MSG_PRINTED}" -eq 0 ]]; then
            log "Non-interactive install detected; HTTPS setup skipped (set SHIFTER_ENABLE_HTTPS=y to force)."
            NONINTERACTIVE_MSG_PRINTED=1
        fi
        return
    fi

    choice="$(printf '%s' "${answer}" | tr '[:upper:]' '[:lower:]')"

    case "${choice}" in
        y|yes)
            if [[ -n "${SHIFTER_DOMAIN:-}" ]]; then
                CERT_DOMAIN="${SHIFTER_DOMAIN}"
            elif [[ "${INSTALLER_INTERACTIVE}" -eq 1 ]]; then
                if ! read -r -p "Domain name: " CERT_DOMAIN <"${INSTALLER_TTY}" 2>/dev/null; then
                    CERT_DOMAIN=""
                fi
            else
                error "HTTPS requested but SHIFTER_DOMAIN not provided in non-interactive mode."
                return
            fi
            CERT_DOMAIN="$(printf '%s' "${CERT_DOMAIN}" | xargs || true)"
            if [[ -z "${CERT_DOMAIN}" ]]; then
                log "No domain provided; skipping HTTPS setup."
                return
            fi
            if [[ -n "${SHIFTER_CONTACT_EMAIL:-}" ]]; then
                CERT_EMAIL="${SHIFTER_CONTACT_EMAIL}"
            elif [[ "${INSTALLER_INTERACTIVE}" -eq 1 ]]; then
                if ! read -r -p "Contact email for Let's Encrypt: " CERT_EMAIL <"${INSTALLER_TTY}" 2>/dev/null; then
                    CERT_EMAIL=""
                fi
            else
                error "HTTPS requested but SHIFTER_CONTACT_EMAIL not provided in non-interactive mode."
                return
            fi
            CERT_EMAIL="$(printf '%s' "${CERT_EMAIL}" | xargs || true)"
            if [[ -z "${CERT_EMAIL}" ]]; then
                log "No contact email provided; skipping HTTPS setup."
                return
            fi

            require_command certbot certbot certbot certbot

            log "Requesting Let's Encrypt certificate for ${CERT_DOMAIN}..."
            if certbot certonly --standalone --preferred-challenges http --keep-until-expiring --non-interactive --agree-tos -d "${CERT_DOMAIN}" -m "${CERT_EMAIL}"; then
                CERTBOT_ENABLED=1
                CERT_FULLCHAIN="/etc/letsencrypt/live/${CERT_DOMAIN}/fullchain.pem"
                CERT_PRIVKEY="/etc/letsencrypt/live/${CERT_DOMAIN}/privkey.pem"
                if [[ ! -f "${CERT_FULLCHAIN}" || ! -f "${CERT_PRIVKEY}" ]]; then
                    error "Certificate files not found after certbot run. Expected ${CERT_FULLCHAIN} and ${CERT_PRIVKEY}."
                    CERT_DOMAIN=""
                    CERT_EMAIL=""
                    CERT_FULLCHAIN=""
                    CERT_PRIVKEY=""
                    CERTBOT_ENABLED=0
                    return
                fi
                update_auth_cert_paths
                log "Certificates obtained and paths recorded."
            else
                error "Certbot failed to issue a certificate for ${CERT_DOMAIN}."
                CERT_DOMAIN=""
                CERT_EMAIL=""
                CERT_FULLCHAIN=""
                CERT_PRIVKEY=""
            fi
            ;;
        *)
            log "HTTPS setup skipped."
            ;;
    esac
}

ensure_pip

load_base_path
log "Using WebUI base path: ${BASE_PATH}"

if [[ -d "${TARGET_DIR}/.git" ]]; then
    log "Repository already present at ${TARGET_DIR}. Pulling latest changes..."
    git -C "${TARGET_DIR}" fetch --all --tags
    git -C "${TARGET_DIR}" pull --ff-only
else
    log "Cloning Shifter Toolkit into ${TARGET_DIR}..."
    git clone --branch "${DEFAULT_BRANCH}" --single-branch "${REPO_URL}" "${TARGET_DIR}"
fi

local_version="unknown"
if [[ -d "${TARGET_DIR}/.git" ]]; then
    local_version="$(git -C "${TARGET_DIR}" rev-parse --short HEAD || echo 'unknown')"
fi
printf '%s\n' "${local_version}" > "${VERSION_FILE}"

printf '%s\n' "${BASE_PATH}" > "${BASE_PATH_FILE}"

log "Installing Python dependencies..."
python3 -m pip install --upgrade pip setuptools wheel

log "Installing Shifter Toolkit in editable mode..."
python3 -m pip install -e "${TARGET_DIR}"

generate_credentials
maybe_configure_https

detect_host_hint() {
    local host_ip=""

    if command -v ip >/dev/null 2>&1; then
        host_ip="$(ip route get 8.8.8.8 2>/dev/null | awk 'NR==1{for(i=1;i<=NF;i++){if($i=="src"){print $(i+1); exit}}}')"
    fi

    if [[ -z "${host_ip}" ]] && command -v hostname >/dev/null 2>&1; then
        host_ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
    fi

    if [[ -z "${host_ip}" ]]; then
        host_ip="$(hostname -f 2>/dev/null || echo localhost)"
    fi

    printf '%s\n' "${host_ip}"
}

cleanup_stale_pid() {
    if [[ -f "${PID_FILE}" ]]; then
        local old_pid
        old_pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
        if [[ -n "${old_pid}" ]] && ! kill -0 "${old_pid}" 2>/dev/null; then
            rm -f "${PID_FILE}"
        fi
    fi
}

stop_existing_daemon() {
    if [[ -f "${PID_FILE}" ]]; then
        local running_pid
        running_pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
        if [[ -n "${running_pid}" ]] && kill -0 "${running_pid}" 2>/dev/null; then
            log "Stopping existing WebUI daemon (PID ${running_pid})..."
            kill "${running_pid}" 2>/dev/null || true
            sleep 2
            if kill -0 "${running_pid}" 2>/dev/null; then
                log "Existing daemon still running; forcing termination."
                kill -9 "${running_pid}" 2>/dev/null || true
                sleep 1
            fi
            rm -f "${PID_FILE}"
        fi
    fi
}

start_daemon() {
    if ! command -v shifter-toolkit >/dev/null 2>&1; then
        log "Cannot locate 'shifter-toolkit' in PATH. Skipping background start."
        return 1
    fi

    stop_existing_daemon
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
    local env_prefix=(env SHIFTER_CONFIG_DIR="${CONFIG_DIR}")
    if [[ "${CERTBOT_ENABLED}" -eq 1 ]]; then
        env_prefix+=(SHIFTER_SESSION_SECURE="true")
    fi
    nohup "${env_prefix[@]}" shifter-toolkit serve --host 0.0.0.0 --port 2063 --base-path "${BASE_PATH}" >"${LOG_FILE}" 2>&1 &
    local new_pid=$!
    sleep 1
    if kill -0 "${new_pid}" 2>/dev/null; then
        echo "${new_pid}" > "${PID_FILE}"
        log "WebUI started in background with PID ${new_pid}."
        local visit_host="${CERT_DOMAIN:-$(detect_host_hint)}"
        local protocol="http"
        if [[ "${CERTBOT_ENABLED}" -eq 1 ]]; then
            protocol="https"
        fi
        log "Visit: ${protocol}://${visit_host}:2063${BASE_PATH}"
    else
        log "Failed to start WebUI daemon. Check ${LOG_FILE} for details."
        return 1
    fi
}

launch_env="SHIFTER_CONFIG_DIR='${CONFIG_DIR}'"
if [[ "${CERTBOT_ENABLED}" -eq 1 ]]; then
    launch_env="${launch_env} SHIFTER_SESSION_SECURE='true'"
fi

if [[ "$(id -u)" -eq 0 ]]; then
    start_daemon || true
else
    log "Run this script with sudo/root if you want the WebUI to start as a daemon automatically."
    log "You can manually launch it with:"
    echo "  sudo ${launch_env} shifter-toolkit serve --host 0.0.0.0 --port 2063 --base-path '${BASE_PATH}' &> ${LOG_FILE} &"
fi

if [[ "${CERTBOT_ENABLED}" -eq 1 ]]; then
    HOST_HINT="${CERT_DOMAIN}"
else
    HOST_HINT="$(detect_host_hint)"
fi
PROTOCOL="http"
if [[ "${CERTBOT_ENABLED}" -eq 1 ]]; then
    PROTOCOL="https"
fi

cat <<EOF

Installation complete!

To run the Web UI manually:
  sudo ${launch_env} shifter-toolkit serve --host 0.0.0.0 --port 2063 --base-path '${BASE_PATH}'

To open the CLI help:
  shifter-toolkit --help

Background service PID file:
  ${PID_FILE}
Log file:
  ${LOG_FILE}

Project directory: ${TARGET_DIR}
Web UI path: ${BASE_PATH}
Endpoint example:
  ${PROTOCOL}://${HOST_HINT}:2063${BASE_PATH}
Credentials file:
  ${AUTH_FILE}
Base path record:
  ${BASE_PATH_FILE}
Credential reset command:
  sudo shifter-toolkit reset-credentials
EOF

if [[ "${CERTBOT_ENABLED}" -eq 1 ]]; then
cat <<EOF

Certificate paths (stored in auth.json):
  fullchain: ${CERT_FULLCHAIN}
  privkey: ${CERT_PRIVKEY}
EOF
fi

if [[ -n "${GENERATED_USERNAME}" && -n "${GENERATED_PASSWORD}" ]]; then
cat <<EOF

Generated WebUI credentials (store securely):
  Username: ${GENERATED_USERNAME}
  Password: ${GENERATED_PASSWORD}

EOF
fi

FULL_ACCESS_URL=""
if [[ "${CERTBOT_ENABLED}" -eq 1 && -n "${CERT_DOMAIN}" ]]; then
    FULL_ACCESS_URL="https://${CERT_DOMAIN}:2063"
    if [[ "${BASE_PATH}" != "/" ]]; then
        FULL_ACCESS_URL="${FULL_ACCESS_URL}${BASE_PATH}"
    fi
else
    FULL_ACCESS_URL="http://${HOST_HINT}:2063"
    if [[ "${BASE_PATH}" != "/" ]]; then
        FULL_ACCESS_URL="${FULL_ACCESS_URL}${BASE_PATH}"
    fi
fi

INSTALL_ROOT="$(cd "${TARGET_DIR}" 2>/dev/null && pwd || printf '%s' "${TARGET_DIR}")"

if [[ -n "${GENERATED_USERNAME}" && -n "${GENERATED_PASSWORD}" ]]; then
    ACCESS_CREDS="$(cat <<EOF
Username: ${GENERATED_USERNAME}
Password: ${GENERATED_PASSWORD}
EOF
)"
else
    ACCESS_CREDS="$(cat <<'EOF'
Username: (existing)
Password: (existing - unchanged)
EOF
)"
fi

printf '\n\033[32m%s\033[0m\n' "$(cat <<EOF
Full access URL: ${FULL_ACCESS_URL}
Install directory: ${INSTALL_ROOT}
Web UI base path: ${BASE_PATH}
${ACCESS_CREDS}
EOF
)"
