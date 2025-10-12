# 🚀 Shifter Toolkit

[![Version](https://img.shields.io/badge/version-0.1.2-blue.svg)](https://pypi.org/project/shifter-toolkit/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

💎 Shifter is an open-source toolkit with a CLI and built-in WebUI for managing GOST, HAProxy, Xray, and iptables tunnels on Linux.

## ✨ Features

- 🎯 **Unified Control Plane** - Install, inspect, and remove tunnelling services
- 💻 **CLI Interface** - Colorful status output and command groups per service  
- 🌐 **Web Dashboard** - AIOHTTP + Jinja2 powered dashboard
- 📦 **Packaged Templates** - Reproducible deployments without network fetches
- 📚 **PyPI Ready** - Complete packaging with entry points and documentation

## 📋 Requirements

- 🐧 Linux host with `systemd` and `iptables`
- 🐍 Python 3.9+ (CPython recommended)
- 🔐 Root/sudo privileges for system services and firewall rules

## 🚀 Installation

### ⚡ One-Line Installer
```bash
curl -fsSL https://raw.githubusercontent.com/zZedix/Shifter/dev/scripts/install.sh | sudo bash
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

# 🌐 Launch the web dashboard (http://127.0.0.1:2063 by default)
sudo shifter-toolkit serve --host 0.0.0.0 --port 2063

# 🔍 Inspect the health of all managed services
sudo shifter-toolkit status
```

> ⚠️ **Note**: Each sub-command validates that it is executed with root privileges before touching the system.

## 📚 Command Reference

| 🎯 Group | 💻 Example | 📝 Description |
|----------|------------|----------------|
| `serve` | `sudo shifter-toolkit serve --host 0.0.0.0 --port 2063` | Launch the AIOHTTP dashboard |
| `status` | `sudo shifter-toolkit status haproxy` | Show active/enabled state plus parsed configuration details |
| `gost` | `sudo shifter-toolkit gost install --domain example.com --port 8080` | Manage GOST tunnel deployment and forwarding rules |
| `haproxy` | `sudo shifter-toolkit haproxy add --relay-port 8081 --main-server-ip 1.2.3.4 --main-server-port 443` | Configure HAProxy frontends/backends |
| `xray` | `sudo shifter-toolkit xray add --address example.com --port 8443` | Maintain Xray Dokodemo-door inbounds |
| `iptables` | `sudo shifter-toolkit iptables install --main-server-ip 203.0.113.10 --ports 80,443` | Persist and inspect port-forwarding firewall rules |

Run `sudo shifter-toolkit <group> --help` for all arguments on a specific command family.

## 🌐 Web Dashboard

Shifter ships with a lightweight dashboard that mirrors the CLI capabilities.

- 📁 Templates live inside the package (`shifter/web/templates`) so deployments don't rely on external assets
- 🔐 Sessions are backed by encrypted cookies
- 🔑 Set `AIOHTTP_SECRET_KEY` in the environment to supply a persistent key across restarts

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
- **Bitcoin (BTC)**: `bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh`
- **Ethereum (ETH)**: `0x8Fb2c4AF74e072CefC14A4E9927a1F86F1cd492c`
- **Tron (TRX)**: `TD43B2eT7JC8upacMarcmBBGFkjy75QJHK`
- **USDT (BEP20)**: `0x8Fb2c4AF74e072CefC14A4E9927a1F86F1cd492c`
- **TON**: `UQAFTGSc2YRNGQwwuTyD0Q-eB7pB0BNG0yvx5jVYAJWFu-y6`

### Other Ways to Support
- ⭐ **Star the repository** if you find it useful
- 🐛 **Report bugs** and suggest improvements
- 📖 **Improve documentation** and translations
- 🔗 **Share with others** who might benefit

---

<div align="center">

**Made with ❤️ by [zZedix](https://github.com/zZedix)**

*Securing the digital world, one line of code at a time!*

</div>
