# CLI Usage

The Shifter CLI is organised into command groups for each supported service. All commands should be executed with root privileges (e.g. via `sudo`) to ensure they can interact with `systemd` and networking subsystems.

## Conventions
- Flags use long-form names (`--domain`, `--port`, `--main-server-ip`, etc.).
- Passing `--help` to any command or group prints contextual information.
- Colourised output highlights active/enabled states when the terminal supports ANSI colours.

## Global Commands
```bash
sudo shifter-toolkit --help          # top-level command groups
sudo shifter-toolkit --version       # report package version via importlib.metadata
sudo shifter-toolkit status          # aggregate service status overview
sudo shifter-toolkit status gost     # restrict status to a single service
```

## GOST Command Group
```bash
# Install and configure a primary forwarding rule
sudo shifter-toolkit gost install --domain example.com --port 8080

# Add an additional port forward on the existing configuration
sudo shifter-toolkit gost add --domain backup.example.com --port 8081

# List configured rules (also part of `status`)
sudo shifter-toolkit gost status

# Remove a specific rule
sudo shifter-toolkit gost remove --port 8081

# Stop and remove all GOST assets and systemd units
sudo shifter-toolkit gost uninstall
```

## HAProxy Command Group
```bash
sudo shifter-toolkit haproxy install \
  --relay-port 8080 \
  --main-server-ip 203.0.113.10 \
  --main-server-port 443

sudo shifter-toolkit haproxy add \
  --relay-port 8081 \
  --main-server-ip 203.0.113.20 \
  --main-server-port 80

sudo shifter-toolkit haproxy remove --frontend-name tunnel-8081
sudo shifter-toolkit haproxy status
sudo shifter-toolkit haproxy uninstall
```

## Xray Command Group
```bash
sudo shifter-toolkit xray install --address example.com --port 443
sudo shifter-toolkit xray add --address example.com --port 8443
sudo shifter-toolkit xray remove --port 8443
sudo shifter-toolkit xray status
sudo shifter-toolkit xray uninstall
```

## IPTables Command Group
```bash
sudo shifter-toolkit iptables install --main-server-ip 203.0.113.10 --ports 80,443
sudo shifter-toolkit iptables status
sudo shifter-toolkit iptables uninstall
```

## Exit Codes
- `0` – command completed successfully.
- Non-zero – execution error (see stderr output for details).

## Troubleshooting Tips
- **Permission denied:** rerun with `sudo` or adjust the invoking user's privileges.
- **Binary not found:** ensure system packages (e.g. `haproxy`, `iptables`, `xray`) are installed. The install commands attempt to install these packages automatically when possible.
- **Service not active after restart:** consult `journalctl -u <service>` to review systemd logs.

For additional operational considerations (service-specific expectations, file locations, etc.) see [services.md](services.md).
