# Shifter Documentation

Welcome to the Shifter knowledge base. This site complements the README and provides deep-dive guidance for operators and contributors managing the project.

## Audience
- **System administrators** who provision or maintain network tunnels on Linux hosts.
- **SRE and platform teams** standardising access pathways and proxies.
- **Contributors** packaging or extending Shifter for bespoke infrastructure.

## What Is Shifter?
Shifter is a Python package distributed via PyPI that delivers:

- A `click`-driven CLI front-end for GOST, HAProxy, Xray, and IPTables.
- An AIOHTTP web dashboard backed by Jinja2 templates.
- Bundled configuration templates that remove the need for ad-hoc downloads.

The toolkit relies on `systemd` to manage long-running services and expects to be executed with root privileges when mutating the host.

## Documentation Map
| Topic | Document |
| --- | --- |
| Installation and prerequisites | [installation.md](installation.md) |
| CLI quick start and examples | [usage.md](usage.md) |
| Web dashboard configuration | [web-ui.md](web-ui.md) |
| Service-specific behaviours | [services.md](services.md) |
| Packaging & release checklist | [release-checklist.md](release-checklist.md) |

## Getting Help
- File issues or feature requests on [GitHub](https://github.com/zZedix/Shifter/issues).
- Consult `shifter-toolkit --help` for contextual command information.
