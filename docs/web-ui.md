# Web UI Guide

Shifter bundles an AIOHTTP-powered web dashboard that surfaces the same operations as the CLI with a friendlier interface.

## Launching the Dashboard
```bash
sudo shifter-toolkit serve --host 0.0.0.0 --port 2063 --base-path /admin-panel
```

- `--host` controls the bind address (defaults to `127.0.0.1` for local-only access).
- `--port` is configurable; the default is `2063`.

The process blocks the terminal. Use a process manager or `systemd` unit if you need to keep the dashboard running in production.

## Secret Key Management
Sessions are handled via `aiohttp-session` with encrypted cookies. By default a random key is generated at startup. For deterministic behaviour across restarts set:

```bash
export AIOHTTP_SECRET_KEY="$(python -c 'import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())')"
sudo shifter-toolkit serve --base-path /admin-panel
```

## Features
- Dashboard view summarising active/enabled state for all services.
- Configuration page for installing, adding, removing, or uninstalling resources via forms.
- Flash messages rendered using session storage to indicate success or failure after each action.
- Server-side execution of CLI commands ensures behaviour parity with the command line workflow.

## Templates
HTML templates live under `shifter/web/templates`:
- `base.html` – shared layout and styling.
- `index.html` – dashboard view.
- `configure.html` – configuration forms and removable item listings.

They are packaged with the distribution and loaded using a filesystem loader pointed at the installed package directory, avoiding any reliance on external assets.

## Reverse Proxying
For public exposure consider placing the dashboard behind HAProxy, Nginx, or Caddy:
- Terminate TLS at the proxy.
- Restrict access via authentication (basic auth, OAuth, etc.).
- Forward traffic to Shifter using the host/port combination specified when running `serve`.

## Hardening Suggestions
- Run the dashboard as a dedicated system user with passwordless sudo limited to required commands.
- Monitor web process logs (stdout/stderr) for command errors.
- Regularly rotate the `AIOHTTP_SECRET_KEY` if sessions are long-lived.
