#!/usr/bin/env python3

import os
import json
import subprocess
import requests
import re
import sys
from .config import repository_url, XRAY_CONFIG_PATH, XRAY_BINARY_PATH

def _run_command(command, **kwargs):
    try:
        return subprocess.run(command, check=True, text=True, **kwargs)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error executing command: {' '.join(command if isinstance(command, list) else command)}\n{e}", file=sys.stderr)
        return None

def is_xray_active():
    result = subprocess.run(["systemctl", "is-active", "--quiet", "xray"])
    return result.returncode == 0

def install_xray(address, port):
    if is_xray_active():
        print("Xray is already active. Proceeding with reinstallation...")
    print("Installing Xray...")
    install_cmd = 'bash -c "$(curl -sL https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install'
    _run_command(install_cmd, shell=True)
    print("Xray installation completed.")
    try:
        config_url = f"{repository_url}/config/config.json"
        response = requests.get(config_url)
        response.raise_for_status()
        config_data = response.json()
        config_data['inbounds'][1]['port'] = port
        config_data['inbounds'][1]['settings']['address'] = address
        config_data['inbounds'][1]['settings']['port'] = port
        config_data['inbounds'][1]['tag'] = f"inbound-{port}"
        with open(XRAY_CONFIG_PATH, 'w') as f:
            json.dump(config_data, f, indent=4)
        _run_command(["sudo", "systemctl", "restart", "xray"])
        if is_xray_active():
            print("Xray installed and configured successfully.")
        else:
            print("Xray service failed to start.", file=sys.stderr)
    except (requests.RequestException, json.JSONDecodeError, IOError) as e:
        print(f"An error occurred during configuration: {e}", file=sys.stderr)

def get_xray_status_details():
    status = "active" if is_xray_active() else "inactive"
    print(f"Xray Service Status: {status}")
    print("\nConfigured Inbounds (from config.json):")
    inbounds = list_inbounds()
    if not inbounds:
        print("  - No inbounds defined in config.")
        return
    for inbound in inbounds:
        print(f"  - Tag: {inbound['tag']:<15} Port: {inbound['port']:<5} -> Destination: {inbound['destination']}")

def add_another_inbound(address, port):
    if not is_xray_active():
        print("Xray is not active. Please start it before adding an inbound.", file=sys.stderr)
        return
    try:
        with open(XRAY_CONFIG_PATH, 'r') as f:
            config_data = json.load(f)
    except (IOError, json.JSONDecodeError):
        print("Could not read or parse Xray config file.", file=sys.stderr)
        return
    existing_ports = {inbound.get('port') for inbound in config_data['inbounds']}
    if port in existing_ports:
        print(f"Port {port} is already in use. Please choose another.", file=sys.stderr)
        return
    new_inbound = { "listen": None, "port": port, "protocol": "dokodemo-door", "settings": { "address": address, "followRedirect": False, "network": "tcp,udp", "port": port }, "tag": f"inbound-{port}" }
    config_data['inbounds'].append(new_inbound)
    try:
        with open(XRAY_CONFIG_PATH, 'w') as f:
            json.dump(config_data, f, indent=4)
        _run_command(["sudo", "systemctl", "restart", "xray"])
        print("Additional inbound added successfully.")
    except IOError as e:
        print(f"Failed to write to config file: {e}", file=sys.stderr)

def list_inbounds():
    """Parses config.json and returns a list of configured inbounds."""
    if not os.path.exists(XRAY_CONFIG_PATH):
        return []
    try:
        with open(XRAY_CONFIG_PATH, 'r') as f:
            config_data = json.load(f)
        
        inbounds_data = []
        for inbound in config_data.get('inbounds', []):
            if inbound.get('tag') == 'api':
                continue
            tag = inbound.get('tag', 'N/A')
            port = inbound.get('port', 'N/A')
            destination = "N/A"
            if inbound.get('protocol') == 'dokodemo-door':
                address = inbound.get('settings', {}).get('address', 'N/A')
                dest_port = inbound.get('settings', {}).get('port', 'N/A')
                destination = f"{address}:{dest_port}"
            inbounds_data.append({'tag': tag, 'port': port, 'destination': destination})
        return inbounds_data
    except (IOError, json.JSONDecodeError):
        return []

def remove_inbound_by_port(port_to_remove):
    """Removes an inbound configuration by its port number."""
    try:
        port_to_remove = int(port_to_remove)
        with open(XRAY_CONFIG_PATH, 'r') as f:
            config_data = json.load(f)
    except (IOError, json.JSONDecodeError, ValueError) as e:
        print(f"Could not read, parse, or validate port: {e}", file=sys.stderr)
        return

    original_count = len(config_data['inbounds'])
    config_data['inbounds'] = [ib for ib in config_data['inbounds'] if ib.get('port') != port_to_remove]
    
    if len(config_data['inbounds']) == original_count:
        print(f"No inbound found with port {port_to_remove}.", file=sys.stderr)
        return
    
    try:
        with open(XRAY_CONFIG_PATH, 'w') as f:
            json.dump(config_data, f, indent=4)
        _run_command(["sudo", "systemctl", "restart", "xray"])
        print(f"Inbound configuration for port {port_to_remove} removed successfully.")
    except IOError as e:
        print(f"Failed to write config file: {e}", file=sys.stderr)

def uninstall_xray():
    print("Uninstalling Xray...")
    _run_command(["sudo", "systemctl", "disable", "--now", "xray"])
    if os.path.exists(XRAY_CONFIG_PATH):
        try:
            os.remove(XRAY_CONFIG_PATH)
        except OSError as e:
            print(f"Could not remove config file: {e}", file=sys.stderr)
    uninstall_cmd = 'bash -c "$(curl -sL https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ remove'
    _run_command(uninstall_cmd, shell=True)
    print("Xray has been uninstalled.")