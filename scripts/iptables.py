#!/usr/bin/env python3

import os
import subprocess
import re
import sys
from .system_info import get_system_info
from .config import IPTABLES_RULES_PATH, IPTABLES_DIR

def _run_command(command, **kwargs):
    try:
        if 'input' in kwargs:
            kwargs['text'] = True
        return subprocess.run(command, check=True, **kwargs)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error executing command: {' '.join(command)}\n{e}", file=sys.stderr)
        return None

def _get_iptables_persistence_info():
    """Returns the correct persistence package and service name based on the OS."""
    info = get_system_info()
    if info['package_manager'] == 'apt':
        return {'package': 'iptables-persistent', 'service': 'netfilter-persistent'}
    elif info['package_manager'] in ['dnf', 'yum']:
        return {'package': 'iptables-services', 'service': 'iptables'}
    else:
        return {'package': 'iptables-persistent', 'service': 'iptables'}

def install_iptables(main_server_ip, ports):
    try:
        sys_info = get_system_info()
        package_manager = sys_info['package_manager']
        persistence = _get_iptables_persistence_info()

        print(f"Installing iptables and persistence package ({persistence['package']})...")
        if package_manager == 'apt':
            _run_command(["sudo", "debconf-set-selections"], input="iptables-persistent iptables-persistent/autosave_v4 boolean true")
            _run_command(["sudo", "debconf-set-selections"], input="iptables-persistent iptables-persistent/autosave_v6 boolean true")

        _run_command(["sudo", package_manager, "install", "iptables", persistence['package'], "-y"], capture_output=True, text=True)

        print("Enabling IP forwarding...")
        _run_command(["sudo", "sysctl", "net.ipv4.ip_forward=1"], capture_output=True, text=True)

        print("Configuring iptables rules...")
        rules = [
            ["sudo", "iptables", "-t", "nat", "-A", "POSTROUTING", "-p", "tcp", "--match", "multiport", "--dports", ports, "-j", "MASQUERADE"],
            ["sudo", "iptables", "-t", "nat", "-A", "PREROUTING", "-p", "tcp", "--match", "multiport", "--dports", ports, "-j", "DNAT", "--to-destination", main_server_ip],
            ["sudo", "iptables", "-t", "nat", "-A", "POSTROUTING", "-p", "udp", "--match", "multiport", "--dports", ports, "-j", "MASQUERADE"],
            ["sudo", "iptables", "-t", "nat", "-A", "PREROUTING", "-p", "udp", "--match", "multiport", "--dports", ports, "-j", "DNAT", "--to-destination", main_server_ip]
        ]
        for rule in rules:
            _run_command(rule, capture_output=True, text=True)

        print("Saving iptables rules...")
        os.makedirs(IPTABLES_DIR, exist_ok=True)
        
        save_result = _run_command(["sudo", "iptables-save"], capture_output=True, text=True)
        if save_result and save_result.stdout:
            with open(IPTABLES_RULES_PATH, 'w') as f:
                f.write(save_result.stdout)
        
        print(f"Enabling and starting {persistence['service']} service...")
        _run_command(["sudo", "systemctl", "enable", "--now", persistence['service']])

        print("IPTables installation and configuration completed.")
    except (OSError, KeyError, subprocess.CalledProcessError) as e:
        print(f"An error occurred: {e}", file=sys.stderr)

def get_iptables_status_details():
    """Prints a detailed status including service name and configured rules."""
    persistence = _get_iptables_persistence_info()
    status_result = subprocess.run(["sudo", "systemctl", "is-active", persistence['service']], capture_output=True, text=True)
    status = status_result.stdout.strip()
    print(f"IPTables Persistence Service ({persistence['service']}) Status: {status}")

    save_result = _run_command(["sudo", "iptables-save"], capture_output=True, text=True)
    if not (save_result and save_result.stdout):
        print("Could not retrieve iptables rules.")
        return

    print("\nActive Port Forwarding Rules:")
    found_rules = False
    for line in save_result.stdout.splitlines():
        if "-A PREROUTING" in line and "-j DNAT" in line:
            proto_match = re.search(r"-p\s+(tcp|udp)", line)
            dports_match = re.search(r"--dports\s+([\d,]+)", line)
            dest_match = re.search(r"--to-destination\s+([\d\.]+)", line)
            if proto_match and dports_match and dest_match:
                found_rules = True
                protocol, dports, dest_ip = proto_match.groups()
                for port in dports.split(','):
                    print(f"  - Port(s) {port} ({protocol.upper()}) -> {dest_ip}")
    
    if not found_rules:
        print("  - No active forwarding rules found.")

def uninstall_iptables():
    persistence = _get_iptables_persistence_info()
    package_manager = get_system_info()['package_manager']

    print("Flushing all iptables rules...")
    commands = [["sudo", "iptables", "-F"], ["sudo", "iptables", "-X"], ["sudo", "iptables", "-t", "nat", "-F"], ["sudo", "iptables", "-t", "nat", "-X"]]
    for cmd in commands:
        _run_command(cmd)

    if os.path.exists(IPTABLES_RULES_PATH):
        try:
            print(f"Removing {IPTABLES_RULES_PATH}...")
            os.remove(IPTABLES_RULES_PATH)
        except OSError as e:
            print(f"Error removing rules file: {e}", file=sys.stderr)

    print(f"Stopping and disabling {persistence['service']} service...")
    subprocess.run(["sudo", "systemctl", "disable", "--now", persistence['service']], capture_output=True)
    
    print(f"Purging persistence package ({persistence['package']})...")
    _run_command(["sudo", package_manager, "purge", persistence['package'], "-y"])

    print("IPTables rules and persistence have been cleared.")