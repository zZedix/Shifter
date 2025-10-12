#!/usr/bin/env python3

import platform
import os

def get_system_info():
    system_info = {}
    
    if os.path.exists('/etc/redhat-release'):
        with open('/etc/redhat-release') as f:
            release_info = f.read()
            if "Rocky" in release_info:
                distro_id = "rocky"
            elif "AlmaLinux" in release_info:
                distro_id = "almalinux"
            else:
                distro_id = "centos"
    elif os.path.exists('/etc/os-release'):
        with open('/etc/os-release') as f:
            lines = f.readlines()
            info_dict = dict(line.strip().split('=', 1) for line in lines if '=' in line)
            distro_id = info_dict.get('ID', '').strip('"')
    else:
        distro_id = platform.system().lower()

    if distro_id in ["ubuntu", "debian"]:
        system_info['package_manager'] = "apt"
        system_info['service_manager'] = "systemctl"
    elif distro_id in ["rocky", "almalinux", "fedora"]:
        system_info['package_manager'] = "dnf"
        system_info['service_manager'] = "systemctl"
    elif distro_id == "centos":
        system_info['package_manager'] = "yum"
        system_info['service_manager'] = "systemctl"
    else:
        raise OSError(f"Unsupported OS: {distro_id}")

    return system_info

if __name__ == '__main__':
    try:
        info = get_system_info()
        print(f"Package Manager: {info['package_manager']}")
        print(f"Service Manager: {info['service_manager']}")
    except OSError as e:
        print(e)