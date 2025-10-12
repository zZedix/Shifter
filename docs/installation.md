# Installation Guide

This document covers supported environments, package installation methods, and post-install verification steps.

## Supported Platforms
- **Operating system:** Linux distributions with `systemd` (Ubuntu, Debian, Rocky, AlmaLinux, Fedora, CentOS Stream).
- **Python:** CPython 3.9+.
- **Privileges:** Root or sudo access is required for all commands that touch services or firewall rules.

## Prerequisites
1. Ensure `python3` and `pip` are available:
   ```bash
   python3 --version
   python3 -m pip --version
   ```
2. Update system packages (recommended):
   ```bash
   sudo apt update && sudo apt upgrade -y      # Debian/Ubuntu
   sudo dnf upgrade --refresh -y               # Fedora/Rocky/AlmaLinux
   ```

## Installing from PyPI
```bash
python -m pip install --upgrade pip
python -m pip install shifter-toolkit
```

Verify the installation:
```bash
shifter-toolkit --version
python -m shifter --help
```

## Installing from Source
```bash
git clone https://github.com/zZedix/Shifter.git
cd Shifter
python -m pip install --upgrade pip
python -m pip install -e .
```

Editable installs expose the package in-place so you can modify the code without reinstalling.

## Optional: Creating a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install shifter-toolkit
```

Deactivate when finished:
```bash
deactivate
```

## Post-install Checklist
- `shifter-toolkit --help` shows the CLI usage information.
- `shifter-toolkit status` prompts for sudo if not already run with elevated privileges.
- `python -m shifter serve --help` works without errors.

If any command fails due to missing privileges or binaries, re-run with `sudo` or consult [usage.md](usage.md) for additional context.
