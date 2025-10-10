# Shifter
Web UI for Port Shifter

## Installation

You can install the CLI as a package once the source is available locally:

```bash
python -m pip install .
```

If you are working in an offline environment, build the wheel without downloading dependencies:

```bash
python -m pip wheel . -w dist --no-build-isolation --no-deps
python -m pip install dist/port_shifter-0.1.0-py3-none-any.whl
```

After installation the `shifter` command is available system-wide.

## To-Do

- [x] Implement/verify services status check (active/inactive)
- [x] Develop better CLI flags for uninstall command
- [x] build as pip package
- [x] update scripts to load better configuration for webui  
- [x] write web ui
- [x] add udp to gost
