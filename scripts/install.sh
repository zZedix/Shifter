#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# Shifter Toolkit installer
# ------------------------------------------------------------

SCRIPT_NAME="Shifter Toolkit installer"
INSTALL_PREFIX="/opt/shifter"
VENV_PATH="${INSTALL_PREFIX}/venv"
SERVICE_NAME="shifter-webui"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SHIFTER_USER="shifter"
PYTHON_BIN="python3"

log() {
    printf '[%s] %s\n' "${SCRIPT_NAME}" "$*"
}

error() {
    printf '[%s] ERROR: %s\n' "${SCRIPT_NAME}" "$*" >&2
}

require_root() {
    if [[ "$(id -u)" -ne 0 ]]; then
        error "This installer must be run as root. Example: sudo bash ${0}"
        exit 1
    fi
}

detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO_ID="${ID:-unknown}"
        DISTRO_LIKE="${ID_LIKE:-}"
    else
        error "Unable to detect distribution. /etc/os-release missing."
        exit 1
    fi
}

install_packages_debian() {
    apt-get update -y
    apt-get install -y python3 python3-venv python3-pip python3-dev build-essential \
        systemd openssl curl git
}

install_packages_centos() {
    local pkg_mgr="yum"
    if command -v dnf >/dev/null 2>&1; then
        pkg_mgr="dnf"
    fi
    ${pkg_mgr} install -y python3 python3-virtualenv python3-pip python3-devel gcc \
        systemd openssl curl git
}

install_packages_arch() {
    pacman -Sy --noconfirm python python-pip python-virtualenv base-devel \
        systemd openssl curl git
}

install_dependencies() {
    log "Installing system dependencies..."
    case "${DISTRO_ID}" in
        ubuntu|debian)
            install_packages_debian
            ;;
        centos|rhel|rocky|almalinux|fedora)
            install_packages_centos
            ;;
        arch|manjaro)
            install_packages_arch
            ;;
        *)
            if [[ "${DISTRO_LIKE}" == *"debian"* ]]; then
                install_packages_debian
            elif [[ "${DISTRO_LIKE}" == *"rhel"* || "${DISTRO_LIKE}" == *"fedora"* ]]; then
                install_packages_centos
            else
                error "Unsupported distribution: ${DISTRO_ID}. Install dependencies manually and re-run."
                exit 1
            fi
            ;;
    esac
}

ensure_user() {
    if ! id "${SHIFTER_USER}" >/dev/null 2>&1; then
        log "Creating system user '${SHIFTER_USER}'..."
        useradd --system --create-home --home-dir "/var/lib/${SHIFTER_USER}" \
            --shell /usr/sbin/nologin "${SHIFTER_USER}"
    else
        log "User '${SHIFTER_USER}' already exists. Skipping."
    fi
}

create_directories() {
    log "Creating directories..."
    install -d -o "${SHIFTER_USER}" -g "${SHIFTER_USER}" "${INSTALL_PREFIX}"
    install -d -o "${SHIFTER_USER}" -g "${SHIFTER_USER}" /var/log/shifter
    install -d -o "${SHIFTER_USER}" -g "${SHIFTER_USER}" /run/shifter
    local user_home
    user_home="$(su -s /bin/sh - "${SHIFTER_USER}" -c 'printf %s "$HOME"' 2>/dev/null || true)"
    if [[ -n "${user_home}" ]]; then
        install -d -o "${SHIFTER_USER}" -g "${SHIFTER_USER}" "${user_home}/.local/share/shifter/certs"
        install -d -o "${SHIFTER_USER}" -g "${SHIFTER_USER}" "${user_home}/.local/state/shifter"
    fi
}

create_virtualenv() {
    if [[ ! -d "${VENV_PATH}" ]]; then
        log "Creating virtual environment at ${VENV_PATH}..."
        "${PYTHON_BIN}" -m venv "${VENV_PATH}"
    else
        log "Virtual environment already exists. Skipping creation."
    fi
    source "${VENV_PATH}/bin/activate"
    pip install --upgrade pip wheel setuptools
}

install_shifter() {
    source "${VENV_PATH}/bin/activate"
    local script_source="${BASH_SOURCE[0]:-}"
    local script_dir
    if [[ -n "${script_source}" && "${script_source}" != "${0}" ]]; then
        script_dir="$(dirname "$(readlink -f "${script_source}")")"
    else
        script_dir="$(pwd)"
    fi
    local repo_root="${script_dir}/.."
    if [[ -f "${repo_root}/pyproject.toml" && -d "${repo_root}/src/shifter" ]]; then
        log "Detected local repository at ${repo_root}. Installing in editable mode..."
        pip install --upgrade pip wheel setuptools
        pip install --upgrade -e "${repo_root}"
    else
        log "Installing Shifter Toolkit from GitHub..."
        pip install --upgrade "git+https://github.com/zZedix/Shifter.git"
    fi
}

write_systemd_unit() {
    log "Writing systemd unit to ${SERVICE_FILE}..."
    cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Shifter WebUI Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SHIFTER_USER}
Group=${SHIFTER_USER}
Environment=PATH=${VENV_PATH}/bin
WorkingDirectory=${INSTALL_PREFIX}
ExecStart=${VENV_PATH}/bin/shifter-toolkit webui start --host 0.0.0.0 --port 2063 --daemon
ExecStop=${VENV_PATH}/bin/shifter-toolkit webui stop
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
}

configure_firewall() {
    log "Configuring firewall rules for TCP 2063 (if applicable)..."
    if command -v ufw >/dev/null 2>&1; then
        if ! ufw status | grep -q "2063"; then
            ufw allow 2063/tcp || true
        fi
    fi
    if command -v firewall-cmd >/dev/null 2>&1; then
        firewall-cmd --add-port=2063/tcp --permanent || true
        firewall-cmd --reload || true
    fi
}

set_permissions() {
    chown -R "${SHIFTER_USER}:${SHIFTER_USER}" "${INSTALL_PREFIX}"
    chown -R "${SHIFTER_USER}:${SHIFTER_USER}" /var/log/shifter
    chown -R "${SHIFTER_USER}:${SHIFTER_USER}" /run/shifter
}

start_service() {
    log "Starting ${SERVICE_NAME} service..."
    systemctl enable --now "${SERVICE_NAME}"
}

print_summary() {
    local shifter_home
    shifter_home="$(su -s /bin/sh - "${SHIFTER_USER}" -c 'printf %s "$HOME"' 2>/dev/null || echo "/var/lib/${SHIFTER_USER}")"
    local cert_path="${shifter_home}/.local/share/shifter/certs"
    local https_hint=""
    if [[ -d "${cert_path}" ]] && compgen -G "${cert_path}/*.crt" >/dev/null 2>&1; then
        https_hint="https://$(hostname -f 2>/dev/null || echo localhost):2063"
    fi

    cat <<EOF
------------------------------------------------------------
Shifter Toolkit WebUI installation complete!

Web UI available at:
  - HTTP : http://$(hostname -f 2>/dev/null || echo localhost):2063
EOF

    if [[ -n "${https_hint}" ]]; then
        printf "  - HTTPS: %s\n" "${https_hint}"
    else
        printf "  - HTTPS: self-signed certificate generated on first run (if --https used)\n"
    fi

    cat <<'EOF'

Service management:
  sudo systemctl status shifter-webui
  sudo systemctl restart shifter-webui
  sudo systemctl stop shifter-webui

CLI management:
  sudo /opt/shifter/venv/bin/shifter-toolkit webui status
  sudo /opt/shifter/venv/bin/shifter-toolkit webui logs

Uninstall instructions:
  sudo systemctl disable --now shifter-webui
  sudo rm -f /etc/systemd/system/shifter-webui.service
  sudo systemctl daemon-reload
  sudo rm -rf /opt/shifter

------------------------------------------------------------
EOF
}

main() {
    require_root
    detect_distro
    install_dependencies
    ensure_user
    create_directories
    create_virtualenv
    install_shifter
    set_permissions
    write_systemd_unit
    configure_firewall
    start_service
    print_summary
}

main "$@"
