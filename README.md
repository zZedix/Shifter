# Shifter

Shifter is a production-ready toolkit for provisioning and operating secure network tunnels on Linux hosts.  
It combines a `click`-powered command-line interface with an AIOHTTP web dashboard so administrators can manage GOST, HAProxy, Xray, and IPTables configurations from a single, auditable workflow.

## Highlights
- **Unified control plane** for installing, inspecting, and removing tunnelling services.
- **First-class CLI** with colorful status output and command groups per service.
- **Web dashboard** served by `aiohttp` + `aiohttp-jinja2`, including session-based flash messaging.
- **Packaged configuration templates** for reproducible deployments without network fetches.
- **PyPI-friendly packaging** with entry points, documentation, and release automation guidance.

## Requirements
- Linux host with `systemd` and `iptables`.
- Python **3.9 or newer** (CPython).
- Root/sudo privileges for any command that touches system services or firewall rules.

## Installation

### Stable release (recommended)
```bash
python -m pip install shifter-toolkit
```

### From a local clone
```bash
git clone https://github.com/zZedix/Shifter.git
cd Shifter
python -m pip install --upgrade pip
python -m pip install -e .
```

The editable install keeps the CLI and web assets in sync while you iterate on the project.

## Quick Start
```bash
# Review available commands
sudo shifter --help

# Launch the web dashboard (http://127.0.0.1:2063 by default)
sudo shifter serve --host 0.0.0.0 --port 2063

# Inspect the health of all managed services
sudo shifter status
```

Each sub-command validates that it is executed with root privileges before touching the system.

## Command Reference

| Group | Example | Description |
| --- | --- | --- |
| `serve` | `sudo shifter serve --host 0.0.0.0 --port 2063` | Launch the AIOHTTP dashboard. |
| `status` | `sudo shifter status haproxy` | Show active/enabled state plus parsed configuration details. |
| `gost` | `sudo shifter gost install --domain example.com --port 8080` | Manage GOST tunnel deployment and forwarding rules. |
| `haproxy` | `sudo shifter haproxy add --relay-port 8081 --main-server-ip 1.2.3.4 --main-server-port 443` | Configure HAProxy frontends/backends. |
| `xray` | `sudo shifter xray add --address example.com --port 8443` | Maintain Xray Dokodemo-door inbounds. |
| `iptables` | `sudo shifter iptables install --main-server-ip 203.0.113.10 --ports 80,443` | Persist and inspect port-forwarding firewall rules. |

Run `sudo shifter <group> --help` for all arguments on a specific command family.

## Web Dashboard
Shifter ships with a lightweight dashboard that mirrors the CLI capabilities.  
Templates live inside the package (`shifter/web/templates`) so deployments do not rely on external assets.  
Sessions are backed by encrypted cookies; set `AIOHTTP_SECRET_KEY` in the environment to supply a persistent key across restarts.

## Packaged Templates
Installer commands render configuration templates that are bundled with the package:
- `gost.service` for systemd.
- `haproxy.cfg` with placeholder tokens.
- `config.json` base configuration for Xray.

Use `importlib.resources` helpers in `shifter.services.config` if you need custom automation that reuses these bundled files.

## Development
```bash
# Install runtime dependencies
python -m pip install -r requirements.txt

# Install the project in editable mode
python -m pip install -e .

# Optional: run the CLI locally
sudo python -m shifter status
```

We recommend developing inside a virtual environment to isolate dependencies.

## Documentation
Extended guides are available under [`docs/`](docs/index.md), covering deployment patterns, CLI details, and release workflows.

## License
Shifter is released under the [MIT License](LICENSE).
