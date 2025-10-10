# Shifter

Network tunnel management tool supporting GOST, HAProxy, Xray, and IPTables.

## Requirements

- Root/sudo privileges
- Python 3.10+

## Installation

```bash
git clone <repository-url>
cd shifter
python -m pip install .
```

## Usage

All commands require sudo.

### Web UI

```bash
sudo shifter serve --host 0.0.0.0 --port 2063
```

### Status

```bash
sudo shifter status [gost|haproxy|xray|iptables]
```

### GOST

```bash
sudo shifter gost install --domain example.com --port 8080
sudo shifter gost add --domain example.com --port 8081
sudo shifter gost remove --port 8081
sudo shifter gost status
sudo shifter gost uninstall
```

### HAProxy

```bash
sudo shifter haproxy install --relay-port 8080 --main-server-ip 1.2.3.4 --main-server-port 443
sudo shifter haproxy add --relay-port 8081 --main-server-ip 1.2.3.4 --main-server-port 80
sudo shifter haproxy remove --frontend-name frontend_8081
sudo shifter haproxy status
sudo shifter haproxy uninstall
```

### Xray

```bash
sudo shifter xray install --address example.com --port 443
sudo shifter xray add --address example.com --port 80
sudo shifter xray remove --port 80
sudo shifter xray status
sudo shifter xray uninstall
```

### IPTables

```bash
sudo shifter iptables install --main-server-ip 1.2.3.4 --ports 80,443
sudo shifter iptables status
sudo shifter iptables uninstall
```

## Project Structure

```
shifter/
├── cli.py                  # CLI entry point
├── scripts/                # Service management modules
│   ├── gost.py            # GOST tunnel management
│   ├── haproxy.py         # HAProxy tunnel management
│   ├── xray.py            # Xray tunnel management
│   ├── iptables.py        # IPTables rules management
│   ├── status.py          # Service status checker
│   ├── system_info.py     # System information utilities
│   └── config.py          # Configuration handler
├── web/                    # Web UI
│   ├── app.py             # AIOHTTP application
│   ├── routes.py          # API routes
│   └── templates/         # HTML templates
├── config/                 # Service configuration templates
│   ├── gost.service
│   └── haproxy.cfg
├── pyproject.toml         # Package configuration
└── requirements.txt       # Python dependencies
```

## Development

```bash
python -m pip install -e .
```