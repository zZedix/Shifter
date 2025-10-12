# 🚀 Shifter Toolkit

<div align="center">

![Version](https://img.shields.io/badge/version-0.1.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![PyPI](https://img.shields.io/badge/pypi-shifter--toolkit-blue.svg)

**A production-ready toolkit for provisioning and operating secure network tunnels on Linux hosts**

[![Install](https://img.shields.io/badge/install-pip%20install%20shifter--toolkit-blue)](https://pypi.org/project/shifter-toolkit/)
[![GitHub](https://img.shields.io/badge/github-zZedix%2FShifter-black)](https://github.com/zZedix/Shifter)

</div>

---

Shifter Toolkit combines a **click-powered** command-line interface with an **AIOHTTP web dashboard** so administrators can manage GOST, HAProxy, Xray, and IPTables configurations from a single, auditable workflow.

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎯 **Unified Control Plane** | Install, inspect, and remove tunnelling services from one place |
| 🖥️ **First-class CLI** | Colorful status output and command groups per service |
| 🌐 **Web Dashboard** | AIOHTTP + Jinja2 powered dashboard with session-based messaging |
| 📦 **Packaged Templates** | Reproducible deployments without network fetches |
| 📚 **PyPI Ready** | Complete packaging with entry points and documentation |

## 📋 Requirements

- 🐧 **Linux host** with `systemd` and `iptables`
- 🐍 **Python 3.9+** (CPython recommended)
- 🔐 **Root/sudo privileges** for system services and firewall rules

## 🚀 Installation

### 📦 Stable Release (Recommended)
```bash
pip install shifter-toolkit
```

### 🔧 From Source
```bash
git clone https://github.com/zZedix/Shifter.git
cd Shifter
pip install --upgrade pip
pip install -e .
```

> 💡 **Tip**: The editable install keeps the CLI and web assets in sync while you iterate on the project.

## ⚡ Quick Start

```bash
<<<<<<< HEAD
# 📋 Review available commands
sudo shifter-toolkit --help

# 🌐 Launch the web dashboard (http://127.0.0.1:2063 by default)
sudo shifter-toolkit serve --host 0.0.0.0 --port 2063

# 🔍 Inspect the health of all managed services
=======
# Review available commands
sudo shifter-toolkit --help

# Launch the web dashboard (http://127.0.0.1:2063 by default)
sudo shifter-toolkit serve --host 0.0.0.0 --port 2063

# Inspect the health of all managed services
>>>>>>> c11714f26ecb9c71bff0eb8c025a8e62b227b09c
sudo shifter-toolkit status
```

> ⚠️ **Security Note**: Each sub-command validates that it is executed with root privileges before touching the system.

## 📚 Command Reference

<<<<<<< HEAD
| 🎯 Group | 💻 Example | 📝 Description |
|----------|------------|----------------|
| `serve` | `sudo shifter-toolkit serve --host 0.0.0.0 --port 2063` | Launch the AIOHTTP dashboard |
| `status` | `sudo shifter-toolkit status haproxy` | Show active/enabled state plus parsed configuration details |
| `gost` | `sudo shifter-toolkit gost install --domain example.com --port 8080` | Manage GOST tunnel deployment and forwarding rules |
| `haproxy` | `sudo shifter-toolkit haproxy add --relay-port 8081 --main-server-ip 1.2.3.4 --main-server-port 443` | Configure HAProxy frontends/backends |
| `xray` | `sudo shifter-toolkit xray add --address example.com --port 8443` | Maintain Xray Dokodemo-door inbounds |
| `iptables` | `sudo shifter-toolkit iptables install --main-server-ip 203.0.113.10 --ports 80,443` | Persist and inspect port-forwarding firewall rules |

> 💡 **Pro Tip**: Run `sudo shifter-toolkit <group> --help` for all arguments on a specific command family.
=======
| Group | Example | Description |
| --- | --- | --- |
| `serve` | `sudo shifter-toolkit serve --host 0.0.0.0 --port 2063` | Launch the AIOHTTP dashboard. |
| `status` | `sudo shifter-toolkit status haproxy` | Show active/enabled state plus parsed configuration details. |
| `gost` | `sudo shifter-toolkit gost install --domain example.com --port 8080` | Manage GOST tunnel deployment and forwarding rules. |
| `haproxy` | `sudo shifter-toolkit haproxy add --relay-port 8081 --main-server-ip 1.2.3.4 --main-server-port 443` | Configure HAProxy frontends/backends. |
| `xray` | `sudo shifter-toolkit xray add --address example.com --port 8443` | Maintain Xray Dokodemo-door inbounds. |
| `iptables` | `sudo shifter-toolkit iptables install --main-server-ip 203.0.113.10 --ports 80,443` | Persist and inspect port-forwarding firewall rules. |

Run `sudo shifter-toolkit <group> --help` for all arguments on a specific command family.
>>>>>>> c11714f26ecb9c71bff0eb8c025a8e62b227b09c

## 🌐 Web Dashboard

Shifter ships with a **lightweight dashboard** that mirrors the CLI capabilities.

- 📁 **Templates** live inside the package (`shifter/web/templates`) so deployments don't rely on external assets
- 🔐 **Sessions** are backed by encrypted cookies
- 🔑 **Security**: Set `AIOHTTP_SECRET_KEY` in the environment to supply a persistent key across restarts

## 📦 Packaged Templates

Installer commands render **configuration templates** that are bundled with the package:

- 🔧 `gost.service` for systemd
- ⚙️ `haproxy.cfg` with placeholder tokens  
- 📄 `config.json` base configuration for Xray

> 💡 **Developer Note**: Use `importlib.resources` helpers in `shifter.services.config` if you need custom automation that reuses these bundled files.

## 🛠️ Development

```bash
# 📦 Install runtime dependencies
pip install -r requirements.txt

# 🔧 Install the project in editable mode
pip install -e .

# 🚀 Optional: run the CLI locally
sudo python -m shifter status
```

> 🌟 **Recommendation**: Develop inside a virtual environment to isolate dependencies.

## 📖 Documentation

Extended guides are available under [`docs/`](docs/index.md), covering:

- 🚀 Deployment patterns
- 💻 CLI details  
- 🔄 Release workflows

---

## 📄 License

Shifter Toolkit is released under the [MIT License](LICENSE).

---

<div align="center">

**Made with ❤️ by [zZedix](https://github.com/zZedix)**

[![PyPI](https://img.shields.io/badge/pypi-shifter--toolkit-blue)](https://pypi.org/project/shifter-toolkit/)
[![GitHub](https://img.shields.io/badge/github-zZedix%2FShifter-black)](https://github.com/zZedix/Shifter)

</div>
