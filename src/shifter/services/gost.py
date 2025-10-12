#!/usr/bin/env python3

import os
import re
import subprocess
import tarfile
import shutil
import platform
import sys
from collections import defaultdict
import requests

from .config import GOST_INSTALL_DIR, GOST_SERVICE_PATH, load_text_template

GOST_BINARY_PATH = os.path.join(GOST_INSTALL_DIR, "gost")

def _run_command(command, **kwargs):
    try:
        return subprocess.run(command, check=True, text=True, **kwargs)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error executing command: {' '.join(command)}\n{e}", file=sys.stderr)
        return None

def is_gost_active():
    result = subprocess.run(["systemctl", "is-active", "--quiet", "gost"])
    return result.returncode == 0

def install_gost(domain, port):
    if is_gost_active():
        print("GOST service is already installed. Proceeding with reinstallation...")

    try:
        os_map = {'Linux': 'linux', 'Darwin': 'darwin', 'Windows': 'windows'}
        arch_map = {'x86_64': 'amd64', 'aarch64': 'arm64', 'armv7l': 'armv7'}
        system = platform.system()
        arch = platform.machine()
        os_name = os_map.get(system)
        arch_name = arch_map.get(arch)

        if not os_name or not arch_name:
            print(f"Unsupported OS/Arch: {system}/{arch}", file=sys.stderr)
            return

        print("Fetching latest GOST version from GitHub...")
        api_url = "https://api.github.com/repos/go-gost/gost/releases/latest"
        response = requests.get(api_url)
        response.raise_for_status()
        release_data = response.json()
        
        download_url = next((asset.get('browser_download_url') for asset in release_data.get('assets', []) if os_name in asset.get('name', '') and arch_name in asset.get('name', '')), None)
        
        if not download_url:
            print(f"Could not find a GOST release for {os_name}/{arch_name}.", file=sys.stderr)
            return

        print(f"Downloading: {download_url}")
        tmp_archive = "/tmp/gost.tar.gz"
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(tmp_archive, 'wb') as f: shutil.copyfileobj(r.raw, f)
        
        print("Extracting GOST binary...")
        with tarfile.open(tmp_archive, "r:gz") as tar: tar.extract('gost', path='/tmp/')
        
        print(f"Installing GOST to {GOST_INSTALL_DIR}...")
        os.makedirs(GOST_INSTALL_DIR, exist_ok=True)
        shutil.move('/tmp/gost', GOST_BINARY_PATH)
        os.chmod(GOST_BINARY_PATH, 0o755)
        os.remove(tmp_archive)

        print("Writing gost.service from packaged template...")
        service_content = load_text_template("gost.service")
        service_content = service_content.replace("/usr/local/bin/gost", GOST_BINARY_PATH)
        exec_start_line = f"ExecStart={GOST_BINARY_PATH} -L=tcp://:{port}/{domain}:{port} -L=udp://:{port}/{domain}:{port}"
        service_content = re.sub(r"^ExecStart=.*$", exec_start_line, service_content, flags=re.MULTILINE)

        with open(GOST_SERVICE_PATH, "w") as f: f.write(service_content)

        _run_command(["sudo", "systemctl", "daemon-reload"])
        _run_command(["sudo", "systemctl", "enable", "--now", "gost"])

        if is_gost_active(): print("GOST tunnel is installed and active.")
        else: print("GOST service failed to start.", file=sys.stderr)

    except (requests.RequestException, tarfile.TarError, IOError, OSError, KeyError) as e:
        print(f"An error occurred during installation: {e}", file=sys.stderr)

def get_gost_status_details():
    status = "active" if is_gost_active() else "inactive"
    print(f"GOST Service Status: {status}")
    print("\nConfigured Forwarding Rules (from gost.service):")
    rules = list_rules()
    if not rules:
        print("  - No forwarding rules found in configuration.")
        return
    for rule in rules:
        print(f"  - Port: {rule['port']:<5} -> Destination: {rule['domain']}")

def add_port_gost(domain, port):
    if not is_gost_active():
        print("GOST service is not active.", file=sys.stderr)
        return
    try:
        port_check_result = subprocess.run(["sudo", "lsof", "-i", f":{port}"], capture_output=True, text=True)
        if port_check_result.returncode == 0:
            print(f"Port {port} is already in use.", file=sys.stderr)
            return
    except FileNotFoundError as e:
        print(f"Error executing lsof: {e}", file=sys.stderr)
        return
    try:
        with open(GOST_SERVICE_PATH, 'r') as f: content = f.read()
        new_forward_rule = f" -L=tcp://:{port}/{domain}:{port} -L=udp://:{port}/{domain}:{port}"
        if new_forward_rule in content:
            print("This exact rule already exists.", file=sys.stderr)
            return
        new_content = re.sub(r'^(ExecStart=.*)$', f'\\1{new_forward_rule}', content, flags=re.MULTILINE)
        with open(GOST_SERVICE_PATH, 'w') as f: f.write(new_content)
        _run_command(["sudo", "systemctl", "daemon-reload"])
        _run_command(["sudo", "systemctl", "restart", "gost"])
        print("New forwarding rule added to GOST.")
    except IOError as e:
        print(f"Error updating service file: {e}", file=sys.stderr)

def list_rules():
    """Parses gost.service and returns a list of configured rules."""
    if not os.path.exists(GOST_SERVICE_PATH): return []
    try:
        with open(GOST_SERVICE_PATH, 'r') as f: content = f.read()
        exec_line = re.search(r"^ExecStart=.*$", content, re.MULTILINE)
        if not exec_line: return []
        rules_map = defaultdict(set)
        found_rules = re.findall(r'-L=(tcp|udp)://:(\d+)/([^ ]+)', exec_line.group(0))
        for proto, port, dest in found_rules:
            rules_map[(port, dest)].add(proto.upper())
        
        rules_data = []
        for (port, domain), protos in sorted(rules_map.items()):
            proto_str = "/".join(sorted(list(protos)))
            rules_data.append({'port': port, 'domain': domain, 'protocols': proto_str})
        return rules_data
    except IOError:
        return []

def remove_rule_by_port(port_to_remove):
    """Removes a forwarding rule by its port number."""
    try:
        port_to_remove = str(port_to_remove)
        with open(GOST_SERVICE_PATH, 'r') as f: content = f.read()
    except (IOError, ValueError) as e:
        print(f"Could not read service file or validate port: {e}", file=sys.stderr)
        return
    
    domain_to_remove = None
    all_rules = re.findall(r'-L=tcp://:(\d+)/([^ ]+)', content)
    for port, domain in all_rules:
        if port == port_to_remove:
            domain_to_remove = domain
            break

    if domain_to_remove is None:
        print(f"No rule found for port {port_to_remove}.", file=sys.stderr)
        return

    tcp_pattern = f" -L=tcp://:{port_to_remove}/{domain_to_remove}"
    udp_pattern = f" -L=udp://:{port_to_remove}/{domain_to_remove}"
    new_content = content.replace(tcp_pattern, "").replace(udp_pattern, "")

    try:
        with open(GOST_SERVICE_PATH, 'w') as f: f.write(new_content)
        print(f"Removing forwarding rule for port {port_to_remove}...")
        _run_command(["sudo", "systemctl", "daemon-reload"])
        _run_command(["sudo", "systemctl", "restart", "gost"])
        print(f"Rule for port {port_to_remove} has been removed.")
    except IOError as e:
        print(f"Error writing service file: {e}", file=sys.stderr)

def uninstall_gost():
    print("Uninstalling GOST...")
    if is_gost_active():
        _run_command(["sudo", "systemctl", "disable", "--now", "gost"])
    if os.path.exists(GOST_SERVICE_PATH):
        try: os.remove(GOST_SERVICE_PATH)
        except OSError as e: print(f"Could not remove service file: {e}", file=sys.stderr)
    if os.path.exists(GOST_INSTALL_DIR):
        try:
            shutil.rmtree(GOST_INSTALL_DIR)
            print(f"Removed GOST directory: {GOST_INSTALL_DIR}")
        except OSError as e: print(f"Could not remove directory {GOST_INSTALL_DIR}: {e}", file=sys.stderr)
    _run_command(["sudo", "systemctl", "daemon-reload"])
    print("GOST service has been uninstalled.")
