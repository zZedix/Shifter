#!/usr/bin/env python3

import os
import subprocess
import re
import json
import sys
from collections import defaultdict
from .config import GOST_SERVICE_PATH, HAPROXY_CONFIG_PATH, XRAY_CONFIG_PATH
from .system_info import get_system_info

def _run_command(command, **kwargs):
    try:
        return subprocess.run(command, check=True, text=True, capture_output=True, **kwargs)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def _get_iptables_persistence_info():
    """Helper moved here to be self-contained."""
    info = get_system_info()
    if info['package_manager'] == 'apt':
        return {'package': 'iptables-persistent', 'service': 'netfilter-persistent'}
    elif info['package_manager'] in ['dnf', 'yum']:
        return {'package': 'iptables-services', 'service': 'iptables'}
    else:
        return {'package': 'iptables-persistent', 'service': 'iptables'}

def _get_systemd_status(service_name):
    status = {'active': 'inactive', 'enabled': 'disabled'}
    try:
        active_result = subprocess.run(
            ["systemctl", "is-active", "--quiet", service_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if active_result.returncode == 0:
            status['active'] = 'active'
        
        enabled_result = subprocess.run(
            ["systemctl", "is-enabled", "--quiet", service_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if enabled_result.returncode == 0:
            status['enabled'] = 'enabled'
    except FileNotFoundError:
        print("Warning: systemctl not found.", file=sys.stderr)
        status = {'active': 'unknown', 'enabled': 'unknown'}
    return status

def get_gost_status():
    status = _get_systemd_status('gost')
    details = []
    if os.path.exists(GOST_SERVICE_PATH):
        try:
            with open(GOST_SERVICE_PATH, 'r') as f:
                content = f.read()
            exec_line = re.search(r"^ExecStart=.*$", content, re.MULTILINE)
            if exec_line:
                rules_map = defaultdict(set)
                found_rules = re.findall(r'-L=(tcp|udp)://:(\d+)/([^ ]+)', exec_line.group(0))
                for proto, port, dest in found_rules:
                    rules_map[(port, dest)].add(proto.upper())
                
                for (port, dest), protos in sorted(rules_map.items()):
                    proto_str = "/".join(sorted(list(protos)))
                    details.append(f"{proto_str} Port {port} -> {dest}")
        except IOError:
            details.append("Error reading service file.")
    status['details'] = details
    return status

def get_haproxy_status():
    status = _get_systemd_status('haproxy')
    details = []
    if os.path.exists(HAPROXY_CONFIG_PATH):
        try:
            with open(HAPROXY_CONFIG_PATH, 'r') as f:
                content = f.read()
            
            frontend_pattern = re.compile(r"frontend\s+([^\s]+)\n(.*?)(?=\nfrontend|\nbackend|\Z)", re.DOTALL)
            backend_pattern = re.compile(r"backend\s+([^\s]+)\n(.*?)(?=\nfrontend|\nbackend|\Z)", re.DOTALL)
            frontends = {m.group(1): m.group(2) for m in frontend_pattern.finditer(content)}
            backends = {m.group(1): m.group(2) for m in backend_pattern.finditer(content)}

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
                details.append(f"Port {port} ({fe_name}) -> {destination}")
        except IOError:
            details.append("Error reading config file.")
    status['details'] = sorted(details)
    return status

def get_xray_status():
    status = _get_systemd_status('xray')
    details = []
    if os.path.exists(XRAY_CONFIG_PATH):
        try:
            with open(XRAY_CONFIG_PATH, 'r') as f:
                config_data = json.load(f)
            inbounds = config_data.get('inbounds', [])
            for inbound in inbounds:
                if inbound.get('tag') == 'api':
                    continue
                port = inbound.get('port', 'N/A')
                protocol = inbound.get('protocol', 'N/A')
                tag = inbound.get('tag', 'N/A')
                if protocol == 'dokodemo-door':
                    address = inbound.get('settings', {}).get('address', 'N/A')
                    dest_port = inbound.get('settings', {}).get('port', 'N/A')
                    details.append(f"Port {port} ({tag}) -> {address}:{dest_port}")
                else:
                     details.append(f"Port {port} ({tag}) -> Protocol: {protocol}")
        except (json.JSONDecodeError, IOError):
            details.append("Error reading config file.")
    status['details'] = sorted(details)
    return status

def get_iptables_status():
    """Gathers status and port forwarding rules from iptables."""
    persistence = _get_iptables_persistence_info()
    status = _get_systemd_status(persistence['service'])
    details = []
    
    iptables_result = _run_command(["sudo", "iptables-save"])
    if iptables_result:
        rules_map = defaultdict(set)
        for line in iptables_result.stdout.splitlines():
            if "-A PREROUTING" in line and "-j DNAT" in line:
                proto_match = re.search(r"-p\s+(tcp|udp)", line)
                dports_match = re.search(r"--dports\s+([\d,]+)", line)
                dest_match = re.search(r"--to-destination\s+([\d\.]+)", line)

                if proto_match and dports_match and dest_match:
                    protocol = proto_match.group(1).upper()
                    dports = dports_match.group(1)
                    dest_ip = dest_match.group(1)
                    for port in dports.split(','):
                        rules_map[(port, dest_ip)].add(protocol)
        
        for (port, dest_ip), protos in sorted(rules_map.items()):
            proto_str = "/".join(sorted(list(protos)))
            details.append(f"Port(s) {port} ({proto_str}) -> {dest_ip}")

    status['details'] = details
    return status

def get_all_services_status():
    """Orchestrates all detailed status checks and returns a single dictionary."""
    return {
        'gost': get_gost_status(),
        'haproxy': get_haproxy_status(),
        'xray': get_xray_status(),
        'iptables': get_iptables_status(),
    }

if __name__ == '__main__':
    status_data = get_all_services_status()
    print(json.dumps(status_data, indent=4))