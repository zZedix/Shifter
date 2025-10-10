#!/usr/bin/env python3

import os
import sys
import click
from scripts import gost, haproxy, iptables, xray, status as status_module

# --- Main CLI Group ---
@click.group()
def cli():
    """
    Shifter: A comprehensive tool for managing network tunnels and services.
    This tool must be run with sudo privileges.
    """
    if os.geteuid() != 0:
        click.echo("Error: This script requires root privileges. Please run with sudo.", err=True)
        sys.exit(1)

# --- Web UI Command ---
@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind the web server to.')
@click.option('--port', default=2063, type=int, help='Port to run the web server on.')
def serve(host, port):
    """Launch the Shifter web UI dashboard."""
    from web.app import create_app
    from aiohttp import web
    app = create_app()
    click.echo(f"Starting Shifter web UI at http://{host}:{port}")
    web.run_app(app, host=host, port=port)

# --- Status Command ---
def print_detailed_status(service_name, status_data):
    """Helper function to print the new, detailed status output."""
    active_color = "green" if status_data.get("active") == "active" else "red"
    enabled_color = "green" if status_data.get("enabled") == "enabled" else "red"
    
    click.echo(click.style(f"Service: {service_name.upper()}", bold=True, fg="cyan"))
    click.echo(f"  Active:  {click.style(status_data.get('active', 'unknown'), fg=active_color)}")
    click.echo(f"  Enabled: {click.style(status_data.get('enabled', 'unknown'), fg=enabled_color)}")

    details = status_data.get('details')
    if details:
        click.echo("  Configuration Details:")
        for detail in details:
            click.echo(f"    - {detail}")
    click.echo("-" * 20)

@cli.command()
@click.argument('service', required=False, type=click.Choice(['gost', 'haproxy', 'xray', 'iptables'], case_sensitive=False))
def status(service):
    """Check the detailed status of one or all managed services."""
    if service:
        status_func = getattr(status_module, f"get_{service}_status", None)
        if status_func:
            print_detailed_status(service, status_func())
    else:
        all_status = status_module.get_all_services_status()
        for name, data in all_status.items():
            print_detailed_status(name, data)


# --- GOST Group ---
@cli.group(name="gost")
def gost_group():
    """Manage GOST tunnel."""
    pass

@gost_group.command("install")
@click.option('--domain', required=True, help='Domain or IP for the tunnel')
@click.option('--port', required=True, type=int, help='Port for the tunnel')
def gost_install(domain, port):
    gost.install_gost(domain=domain, port=port)

@gost_group.command("status")
def gost_status():
    """Show detailed status and configured forwarding rules for GOST."""
    gost.get_gost_status_details()

@gost_group.command("add")
@click.option('--domain', required=True, help='Domain or IP for the new tunnel')
@click.option('--port', required=True, type=int, help='New port for the tunnel')
def gost_add(domain, port):
    gost.add_port_gost(domain=domain, port=port)

@gost_group.command("remove")
@click.option('--port', required=True, type=int, help='The port number of the rule to remove.')
def gost_remove(port):
    """Remove a forwarding rule by port number."""
    gost.remove_rule_by_port(port)

@gost_group.command("uninstall")
def gost_uninstall():
    gost.uninstall_gost()

# --- HAProxy Group ---
@cli.group(name="haproxy")
def haproxy_group():
    """Manage HAProxy tunnel."""
    pass

@haproxy_group.command("install")
@click.option('--relay-port', required=True, type=int, help="This server's free port")
@click.option('--main-server-ip', required=True, help="Destination server's IP or domain")
@click.option('--main-server-port', required=True, type=int, help="Destination server's port")
def haproxy_install(relay_port, main_server_ip, main_server_port):
    haproxy.install_haproxy(relay_port, main_server_ip, main_server_port)

@haproxy_group.command("status")
def haproxy_status():
    haproxy.get_haproxy_status_details()

@haproxy_group.command("add")
@click.option('--relay-port', required=True, type=int, help="This server's new free port")
@click.option('--main-server-ip', required=True, help="New destination server's IP or domain")
@click.option('--main-server-port', required=True, type=int, help="New destination server's port")
def haproxy_add(relay_port, main_server_ip, main_server_port):
    haproxy.add_frontend_backend(relay_port, main_server_ip, main_server_port)

@haproxy_group.command("remove")
@click.option('--frontend-name', required=True, help='The name of the frontend to remove.')
def haproxy_remove(frontend_name):
    """Remove a tunnel by its frontend name."""
    haproxy.remove_tunnel(frontend_name)

@haproxy_group.command("uninstall")
def haproxy_uninstall():
    haproxy.uninstall_haproxy()

# --- Xray Group ---
@cli.group(name="xray")
def xray_group():
    """Manage Xray (Dokodemo-door)."""
    pass

@xray_group.command("install")
@click.option('--address', required=True, help='Domain or IP for the inbound')
@click.option('--port', required=True, type=int, help='Port for the inbound')
def xray_install(address, port):
    xray.install_xray(address=address, port=port)

@xray_group.command("status")
def xray_status():
    """Show detailed status and configured inbounds for Xray."""
    xray.get_xray_status_details()

@xray_group.command("add")
@click.option('--address', required=True, help='Domain or IP for the new inbound')
@click.option('--port', required=True, type=int, help='New port for the inbound')
def xray_add(address, port):
    xray.add_another_inbound(address=address, port=port)

@xray_group.command("remove")
@click.option('--port', required=True, type=int, help='The port number of the inbound to remove.')
def xray_remove(port):
    """Remove an inbound by its port number."""
    xray.remove_inbound_by_port(port)

@xray_group.command("uninstall")
def xray_uninstall():
    xray.uninstall_xray()

# --- IPTables Group ---
@cli.group(name="iptables")
def iptables_group():
    """Manage IPTables rules."""
    pass

@iptables_group.command("install")
@click.option('--main-server-ip', required=True, help="Destination server's IP")
@click.option('--ports', required=True, help="Comma-separated list of ports (e.g., 80,443)")
def iptables_install(main_server_ip, ports):
    iptables.install_iptables(main_server_ip, ports)

@iptables_group.command("status")
def iptables_status():
    """Show detailed status and configured forwarding rules for IPTables."""
    iptables.get_iptables_status_details()

@iptables_group.command("uninstall")
def iptables_uninstall():
    iptables.uninstall_iptables()

if __name__ == "__main__":
    cli()