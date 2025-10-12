#!/usr/bin/env python3

import os
import re
import subprocess
import shutil
import sys

from .config import HAPROXY_CONFIG_PATH, load_text_template
from .system_info import get_system_info

def _run_command(command, **kwargs):
    try:
        return subprocess.run(command, check=True, text=True, **kwargs)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error executing command: {' '.join(command)}\n{e}", file=sys.stderr)
        return None

def is_haproxy_active():
    result = subprocess.run(["systemctl", "is-active", "--quiet", "haproxy"])
    return result.returncode == 0

def install_haproxy(relay_port, main_server_ip, main_server_port):
    if is_haproxy_active():
        print("HAProxy is already active. Proceeding with reinstallation...")
    try:
        package_manager = get_system_info()['package_manager']
        print("Installing HAProxy...")
        _run_command(["sudo", package_manager, "install", "haproxy", "-y"], capture_output=True)
        print("Writing haproxy.cfg from packaged template...")
        template_content = load_text_template("haproxy.cfg")
        temp_path = "/tmp/haproxy.cfg"
        with open(temp_path, 'w') as f:
            f.write(template_content)
        shutil.move(temp_path, HAPROXY_CONFIG_PATH)
        print(f"Moved new haproxy.cfg to {HAPROXY_CONFIG_PATH}")
    except (OSError, requests.RequestException, KeyError) as e:
        print(f"An error occurred during installation: {e}", file=sys.stderr)
        return
    print("Configuring HAProxy...")
    try:
        with open(HAPROXY_CONFIG_PATH, 'r') as f:
            content = f.read()
        content = content.replace("$iport", str(relay_port))
        content = content.replace("$IP", main_server_ip)
        content = content.replace("$port", str(main_server_port))
        with open(HAPROXY_CONFIG_PATH, 'w') as f:
            f.write(content)
        _run_command(["sudo", "systemctl", "enable", "haproxy"])
        _run_command(["sudo", "systemctl", "restart", "haproxy"])
        if is_haproxy_active():
            print("HAProxy tunnel is installed and active.")
        else:
            print("HAProxy service failed to start.", file=sys.stderr)
    except IOError as e:
        print(f"Error configuring HAProxy: {e}", file=sys.stderr)

def get_haproxy_status_details():
    status = "active" if is_haproxy_active() else "inactive"
    print(f"HAProxy Service Status: {status}")
    print("\nConfigured Tunnels (from haproxy.cfg):")
    tunnels = list_tunnels()
    if not tunnels:
        print("  - No tunnels defined in config.")
        return
    for tunnel in tunnels:
        print(f"  - Frontend: {tunnel['frontend']:<25} Port: {tunnel['port']:<5} -> Destination: {tunnel['destination']}")

def add_frontend_backend(relay_port, main_server_ip, main_server_port):
    if not is_haproxy_active():
        print("HAProxy service is not active. Please start it first.", file=sys.stderr)
        return
    with open(HAPROXY_CONFIG_PATH, 'r') as f:
        if f"frontend tunnel-{relay_port}" in f.read():
            print(f"Port {relay_port} is already in use by HAProxy. Choose another.", file=sys.stderr)
            return
    new_config = f"""
frontend tunnel-{relay_port}
    bind :::{relay_port} v4v6
    mode tcp
    default_backend tunnel-{main_server_ip}-{main_server_port}

backend tunnel-{main_server_ip}-{main_server_port}
    mode tcp
    server target_server {main_server_ip}:{main_server_port}
"""
    try:
        with open(HAPROXY_CONFIG_PATH, 'a') as f:
            f.write(new_config)
        _run_command(["sudo", "systemctl", "restart", "haproxy"])
        print("New frontend and backend added successfully.")
    except IOError as e:
        print(f"Error updating HAProxy configuration: {e}", file=sys.stderr)

def list_tunnels():
    """Parses haproxy.cfg and returns a list of configured tunnels."""
    if not os.path.exists(HAPROXY_CONFIG_PATH):
        return []
    try:
        with open(HAPROXY_CONFIG_PATH, 'r') as f:
            content = f.read()
        
        frontend_pattern = re.compile(r"frontend\s+([^\s]+)\n(.*?)(?=\nfrontend|\nbackend|\Z)", re.DOTALL)
        backend_pattern = re.compile(r"backend\s+([^\s]+)\n(.*?)(?=\nfrontend|\nbackend|\Z)", re.DOTALL)
        frontends = {m.group(1): m.group(2) for m in frontend_pattern.finditer(content)}
        backends = {m.group(1): m.group(2) for m in backend_pattern.finditer(content)}
        
        tunnels_data = []
        for fe_name, fe_config in frontends.items():
            bind_match = re.search(r"bind\s+.*?:(\d+)", fe_config)
            backend_match = re.search(r"default_backend\s+([^\s]+)", fe_config)
            port = bind_match.group(1) if bind_match else "N/A"
            be_name = backend_match.group(1) if backend_match else "N/A"
            destination = "N/A"
            if be_name in backends:
                server_match = re.search(r"server\s+\w+\s+([^\s]+)", backends[be_name])
                if server_match:
                    destination = server_match.group(1)
            tunnels_data.append({'frontend': fe_name, 'port': port, 'backend': be_name, 'destination': destination})
        return tunnels_data
    except IOError:
        return []

def remove_tunnel(frontend_name):
    """Removes a frontend and its corresponding backend by the frontend's name."""
    try:
        with open(HAPROXY_CONFIG_PATH, 'r') as f:
            lines = f.readlines()
    except IOError as e:
        print(f"Could not read {HAPROXY_CONFIG_PATH}: {e}", file=sys.stderr)
        return

    content = "".join(lines)
    frontend_block_pattern = re.compile(r"frontend\s+" + re.escape(frontend_name) + r"\n(.*?)(?=\nfrontend|\nbackend|\Z)", re.DOTALL)
    fe_match = frontend_block_pattern.search(content)

    if not fe_match:
        print(f"Frontend '{frontend_name}' not found.", file=sys.stderr)
        return

    backend_match = re.search(r"default_backend\s+([^\s]+)", fe_match.group(0))
    if not backend_match:
        print(f"Could not find backend for frontend '{frontend_name}'.", file=sys.stderr)
        return
    
    backend_to_remove = backend_match.group(1)
    print(f"Removing frontend '{frontend_name}' and backend '{backend_to_remove}'...")

    new_lines = []
    in_fe_block = False
    in_be_block = False
    for line in lines:
        if line.strip() == f"frontend {frontend_name}":
            in_fe_block = True
            continue
        if line.strip() == f"backend {backend_to_remove}":
            in_be_block = True
            continue
        if (in_fe_block or in_be_block) and not line.strip():
            in_fe_block = False
            in_be_block = False
            continue
        if not in_fe_block and not in_be_block:
            new_lines.append(line)

    try:
        with open(HAPROXY_CONFIG_PATH, 'w') as f:
            f.writelines(new_lines)
        _run_command(["sudo", "systemctl", "restart", "haproxy"])
        print("Frontend and backend removed successfully.")
    except IOError as e:
        print(f"Error writing to config file: {e}", file=sys.stderr)

def uninstall_haproxy():
    print("Uninstalling HAProxy...")
    try:
        package_manager = get_system_info()['package_manager']
        _run_command(["sudo", "systemctl", "disable", "--now", "haproxy"], capture_output=True)
        _run_command(["sudo", package_manager, "purge", "haproxy", "-y"], capture_output=True)
        if os.path.exists(HAPROXY_CONFIG_PATH):
            os.remove(HAPROXY_CONFIG_PATH)
        print("HAProxy has been uninstalled.")
    except (OSError, KeyError) as e:
        print(f"An error occurred during uninstallation: {e}", file=sys.stderr)
