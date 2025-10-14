# 🚀 Shifter Toolkit

[![Version](https://img.shields.io/badge/version-0.1.2-blue.svg)](https://pypi.org/project/shifter-toolkit/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A production-ready toolkit for provisioning and operating secure network tunnels on Linux hosts.

## ✨ Features

- 🎯 **Unified Control Panel** - Install, inspect, and remove tunnelling services
- 💻 **CLI Interface** - Colorful status output and command groups per service  
- 🌐 **Web Dashboard** - AIOHTTP + Jinja2 powered dashboard with login
- 🔒 **HTTPS Ready** - Optional Let's Encrypt provisioning during install
- 📦 **Packaged Templates** - Reproducible deployments without network fetches
- 📚 **PyPI Ready** - Complete packaging with entry points and documentation

## 📋 Requirements

- 🐧 Linux host with `systemd` and `iptables`
- 🐍 Python 3.9+ (CPython recommended)
- 🔐 Root/sudo privileges for system services and firewall rules

## 🚀 Installation

### ⚡ Interactive Installer
```bash
curl -fsSL https://raw.githubusercontent.com/zZedix/Shifter/main/scripts/install.sh -o install.sh
chmod +x install.sh
sudo ./install.sh
```
```bash
# First-time credentials (run after installer finishes)
sudo shifter-toolkit reset-credentials --generate
```

### 🔧 From Source
```bash
git clone https://github.com/zZedix/Shifter.git
cd Shifter
pip install -e .
```

## ⚡ Quick Start

```bash
# 📋 Review available commands
sudo shifter-toolkit --help

# 🔐 Create or update WebUI credentials
sudo shifter-toolkit reset-credentials --generate

# 📄 Inspect the stored credential hash (optional)
sudo cat /root/Shifter/config/auth.json

# 🔍 Inspect the health of all managed services
sudo shifter-toolkit status
```

> ⚠️ **Note**: Each sub-command validates that it is executed with root privileges before touching the system.
> 💡 **Installer tip**: The installer writes a unique path slug to `~/Shifter/shifter-webui.basepath`. After the install, run `sudo shifter-toolkit reset-credentials --generate` to create your login and store the hash in `~/Shifter/config/auth.json`. Combine the base path with your host/port (e.g., `https://server:2063$(cat ~/Shifter/shifter-webui.basepath)`) to reach the dashboard.

## 📚 Command Reference

| 🎯 Group | 💻 Example | 📝 Description |
|----------|------------|----------------|
| `serve` | `sudo shifter-toolkit serve --host 0.0.0.0 --port 2063 --base-path /admin-panel` | Launch the AIOHTTP dashboard |
| `status` | `sudo shifter-toolkit status haproxy` | Show active/enabled state plus parsed configuration details |
| `gost` | `sudo shifter-toolkit gost install --domain example.com --port 8080` | Manage GOST tunnel deployment and forwarding rules |
| `haproxy` | `sudo shifter-toolkit haproxy add --relay-port 8081 --main-server-ip 1.2.3.4 --main-server-port 443` | Configure HAProxy frontends/backends |
| `xray` | `sudo shifter-toolkit xray add --address example.com --port 8443` | Maintain Xray Dokodemo-door inbounds |
| `iptables` | `sudo shifter-toolkit iptables install --main-server-ip 203.0.113.10 --ports 80,443` | Persist and inspect port-forwarding firewall rules |

Run `sudo shifter-toolkit <group> --help` for all arguments on a specific command family.

## 🌐 Web Dashboard & Security

Shifter ships with a lightweight dashboard that mirrors the CLI capabilities.

- 📁 Templates live inside the package (`shifter/web/templates`) so deployments don't rely on external assets
- 🔐 Generate credentials with `sudo shifter-toolkit reset-credentials --generate` after installing (hash stored securely in `~/Shifter/config/auth.json`)
- 🔑 Reset credentials any time with `sudo shifter-toolkit reset-credentials` (supports prompts or random generation)
- 🧁 Sessions are backed by encrypted cookies—set `AIOHTTP_SECRET_KEY` to persist the cookie key across restarts
- 🔒 Optional HTTPS provisioning via Let's Encrypt when the installer runs (interactive prompt or `SHIFTER_ENABLE_HTTPS`, `SHIFTER_DOMAIN`, `SHIFTER_CONTACT_EMAIL`)

## 📦 Packaged Templates

Installer commands render configuration templates that are bundled with the package:

- 🔧 `gost.service` for systemd
- ⚙️ `haproxy.cfg` with placeholder tokens  
- 📄 `config.json` base configuration for Xray

Use `importlib.resources` helpers in `shifter.services.config` if you need custom automation that reuses these bundled files.

## 🛠️ Development

```bash
# 📦 Install runtime dependencies
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

# 🔧 Install the project in editable mode
python -m pip install -e .

# 🚀 Optional: run the CLI locally
sudo python -m shifter status
```

We recommend developing inside a virtual environment to isolate dependencies.

## 📖 Documentation

Extended guides are available under [`docs/`](docs/index.md), covering deployment patterns, CLI details, and release workflows.

## 📄 License

Shifter Toolkit is released under the [MIT License](LICENSE).

## 💰 Donations

If you find Shifter Toolkit useful and want to support its development, consider making a donation:

### Cryptocurrency Donations
- **Bitcoin (BTC)**: `bc1q637gahjssmv9g3903j88tn6uyy0w2pwuvsp5k0`
- **Ethereum (ETH)**: `0x5B2eE8970E3B233F79D8c765E75f0705278098a0`
- **Tron (TRX)**: `TSAsosG9oHMAjAr3JxPQStj32uAgAUmMp3`
- **USDT (BEP20)**: `0x5B2eE8970E3B233F79D8c765E75f0705278098a0`
- **TON**: `UQA-95WAUn_8pig7rsA9mqnuM5juEswKONSlu-jkbUBUhku6`

### Other Ways to Support
- ⭐ **Star the repository** if you find it useful
- 🐛 **Report bugs** and suggest improvements
- 📖 **Improve documentation** and translations
- 🔗 **Share with others** who might benefit

---

<div align="center">

**Made with ❤️ by [zZedix](https://github.com/zZedix) and [ReturnFI](https://github.com/ReturnFI)**

*Securing the digital world, one line of code at a time!*

</div>
