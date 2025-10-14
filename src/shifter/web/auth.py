#!/usr/bin/env python3

"""Authentication helpers for the Shifter Web UI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import bcrypt

CONFIG_DIR_ENV = "SHIFTER_CONFIG_DIR"
AUTH_FILE_ENV = "SHIFTER_AUTH_FILE"
HOME_ENV = "SHIFTER_HOME"
DEFAULT_CONFIG_SUBDIR = "config"
AUTH_FILENAME = "auth.json"


class AuthConfigError(RuntimeError):
    """Raised when the authentication configuration is missing or malformed."""


def _expand_path(path: str) -> Path:
    return Path(path).expanduser()


def resolve_config_dir() -> Path:
    """Resolve the configuration directory path."""
    if auth_file_env := os.environ.get(AUTH_FILE_ENV):
        return _expand_path(auth_file_env).parent
    if config_dir_env := os.environ.get(CONFIG_DIR_ENV):
        return _expand_path(config_dir_env)
    home_root = os.environ.get(HOME_ENV)
    if home_root:
        return _expand_path(home_root) / DEFAULT_CONFIG_SUBDIR
    return Path.home() / "Shifter" / DEFAULT_CONFIG_SUBDIR


def resolve_auth_file() -> Path:
    """Return the expected auth.json file path."""
    if auth_file_env := os.environ.get(AUTH_FILE_ENV):
        return _expand_path(auth_file_env)
    return resolve_config_dir() / AUTH_FILENAME


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise AuthConfigError(
            f"Authentication configuration file not found at {path}. "
            "Run the installer to generate credentials."
        ) from exc
    except json.JSONDecodeError as exc:
        raise AuthConfigError(f"Authentication configuration at {path} is not valid JSON.") from exc


class AuthManager:
    """Manager for loading and updating Web UI authentication details."""

    def __init__(self, auth_file: Optional[Path] = None):
        self.auth_file = auth_file or resolve_auth_file()
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        data = _load_json(self.auth_file)
        if "username" not in data or "password_hash" not in data:
            raise AuthConfigError(
                f"Authentication configuration at {self.auth_file} is missing required fields."
            )
        return data

    @property
    def username(self) -> str:
        return self._data["username"]

    @property
    def password_hash(self) -> str:
        return self._data["password_hash"]

    @property
    def cert_paths(self) -> Dict[str, str]:
        return self._data.get("cert_paths", {})

    def verify_password(self, candidate: str) -> bool:
        if not candidate:
            return False
        try:
            hashed = self.password_hash.encode("utf-8")
        except KeyError:
            return False
        return bcrypt.checkpw(candidate.encode("utf-8"), hashed)

    def update_credentials(self, username: str, new_password: str) -> None:
        if not username:
            raise ValueError("Username must not be empty.")
        if not new_password:
            raise ValueError("Password must not be empty.")
        password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        self._data["username"] = username
        self._data["password_hash"] = password_hash
        self._write()

    def update_cert_paths(self, *, fullchain: Optional[str] = None, privkey: Optional[str] = None) -> None:
        cert_paths = self._data.setdefault("cert_paths", {})
        if fullchain is not None:
            cert_paths["fullchain"] = fullchain
        if privkey is not None:
            cert_paths["privkey"] = privkey
        self._write()

    def reload(self) -> None:
        self._data = self._load()

    def _write(self) -> None:
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        with self.auth_file.open("w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=4)
            handle.write("\n")
        try:
            os.chmod(self.auth_file, 0o600)
        except OSError:
            # Non-critical: skip if the platform does not support chmod.
            pass
