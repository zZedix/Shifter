#!/usr/bin/env python3

"""Shared configuration values and helpers for the Shifter services."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

# System destination paths configured by Shifter's installers.
GOST_SERVICE_PATH = "/usr/lib/systemd/system/gost.service"
HAPROXY_CONFIG_PATH = "/etc/haproxy/haproxy.cfg"
IPTABLES_RULES_PATH = "/etc/iptables/rules.v4"
IPTABLES_DIR = "/etc/iptables"
XRAY_CONFIG_PATH = "/usr/local/etc/xray/config.json"
GOST_INSTALL_DIR = "/opt/gost"

_DATA_PACKAGE = "shifter.data"


def load_text_template(filename: str) -> str:
    """Return the contents of a packaged text template."""
    return resources.files(_DATA_PACKAGE).joinpath(filename).read_text(encoding="utf-8")


def load_json_template(filename: str) -> Any:
    """Return the parsed JSON content of a packaged template."""
    with resources.files(_DATA_PACKAGE).joinpath(filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)
