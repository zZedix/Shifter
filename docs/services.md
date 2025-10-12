# Service Behaviour

This document explains how each Shifter service module manipulates system resources and what artifacts are created on the host.

## Common Patterns
- Installation commands call out to the distribution's package manager (`apt`, `dnf`, or `yum`) when required packages are missing.
- Service status is determined via `systemctl is-active` and `systemctl is-enabled`.
- Configuration files are generated from templates bundled with the `shifter` package, eliminating external download dependencies.

All paths below assume default locations. Override them by editing the module constants if you maintain a fork with custom requirements.

## GOST
- **Binary location:** `/opt/gost/gost`
- **Systemd unit:** `/usr/lib/systemd/system/gost.service`
- **Template:** `shifter/data/gost.service`
- **Operations:**
  - Installation fetches the latest release from `github.com/go-gost/gost`, extracts the binary, writes the systemd unit, reloads systemd, and starts the service.
  - Additional forwarding rules append `-L` directives to the `ExecStart` line inside the systemd unit.
  - Removal of a rule deletes matching `tcp`/`udp` snippets and restarts the service.

## HAProxy
- **Config file:** `/etc/haproxy/haproxy.cfg`
- **Template:** `shifter/data/haproxy.cfg`
- **Operations:**
  - Installation ensures `haproxy` is present, writes the packaged config template, substitutes placeholders for the requested relay port and upstream, and enables the service.
  - Additional frontends/backends append new sections for the specified destination.
  - Removal deletes matching frontend/backend blocks and restarts HAProxy.

## Xray
- **Config file:** `/usr/local/etc/xray/config.json`
- **Template:** `shifter/data/config.json`
- **Operations:**
  - Installation delegates binary installation to the official shell script, then writes the templated JSON with updated address/port values.
  - Additional inbounds append a new JSON object with the requested listening parameters.
  - Removal filters out any inbound matching the provided port.

## IPTables
- **Rules file:** `/etc/iptables/rules.v4`
- **Supporting directory:** `/etc/iptables`
- **Services:** The persistence service depends on the distribution (`iptables-persistent`, `netfilter-persistent`, `iptables-services`, or `iptables`).
- **Operations:**
  - Installation enables IP forwarding, creates NAT rules for TCP+UDP, saves rules to disk, and ensures the persistence service is enabled.
  - Status parsing inspects `iptables-save` output and summarises DNAT entries.
  - Uninstallation flushes tables, removes persistence artefacts, disables associated services, and purges the persistence package.

## Status Aggregation
`shifter.services.status` orchestrates the above modules to return a combined dictionary mapping service names to their active/enabled state and parsed configuration details. The CLI and web dashboard consume this data structure for consistent reporting.
