# CLI Usage

The Shifter CLI is organised into command groups for each supported service. All commands should be executed with root privileges (e.g. via `sudo`) to ensure they can interact with `systemd` and networking subsystems.

## Conventions
- Flags use long-form names (`--domain`, `--port`, `--main-server-ip`, etc.).
- Passing `--help` to any command or group prints contextual information.
- Colourised output highlights active/enabled states when the terminal supports ANSI colours.

## Global Commands
```bash
sudo shifter --help          # top-level command groups
sudo shifter --version       # report package version via importlib.metadata
sudo shifter status          # aggregate service status overview
sudo shifter status gost     # restrict status to a single service
```

## GOST Command Group
```bash
# Install and configure a primary forwarding rule
sudo shifter gost install --domain example.com --port 8080

# Add an additional port forward on the existing configuration
sudo shifter gost add --domain backup.example.com --port 8081

# List configured rules (also part of `status`)
sudo shifter gost status

# Remove a specific rule
sudo shifter gost remove --port 8081

# Stop and remove all GOST assets and systemd units
sudo shifter gost uninstall
```

## HAProxy Command Group
```bash
sudo shifter haproxy install \
  --relay-port 8080 \
  --main-server-ip 203.0.113.10 \
  --main-server-port 443

sudo shifter haproxy add \
  --relay-port 8081 \
  --main-server-ip 203.0.113.20 \
  --main-server-port 80

sudo shifter haproxy remove --frontend-name tunnel-8081
sudo shifter haproxy status
sudo shifter haproxy uninstall
```

## Xray Command Group
```bash
sudo shifter xray install --address example.com --port 443
sudo shifter xray add --address example.com --port 8443
sudo shifter xray remove --port 8443
sudo shifter xray status
sudo shifter xray uninstall
```

## IPTables Command Group
```bash
sudo shifter iptables install --main-server-ip 203.0.113.10 --ports 80,443
sudo shifter iptables status
sudo shifter iptables uninstall
```

## Exit Codes
- `0` – command completed successfully.
- Non-zero – execution error (see stderr output for details).

## Troubleshooting Tips
- **Permission denied:** rerun with `sudo` or adjust the invoking user's privileges.
- **Binary not found:** ensure system packages (e.g. `haproxy`, `iptables`, `xray`) are installed. The install commands attempt to install these packages automatically when possible.
- **Service not active after restart:** consult `journalctl -u <service>` to review systemd logs.

For additional operational considerations (service-specific expectations, file locations, etc.) see [services.md](services.md).
