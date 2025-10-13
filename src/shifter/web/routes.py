import sys
import asyncio
from typing import Iterable

from aiohttp import web
from aiohttp_session import get_session
import aiohttp_jinja2

from ..services import gost, haproxy, iptables, status as status_module, xray


def _command_prefix(app: web.Application) -> str:
    return app["base_path_prefix"]


def _with_base_path(app: web.Application, path: str) -> str:
    if path == "/":
        return app["base_path"] if app["base_path"] != "/" else "/"
    prefix = _command_prefix(app)
    if not prefix:
        return path
    return f"{prefix}{path}"


def _strip_base_path(request: web.Request) -> Iterable[str]:
    prefix = _command_prefix(request.app)
    segments = [part for part in request.path.split("/") if part]
    if prefix:
        base_segments = [part for part in prefix.split("/") if part]
        if segments[: len(base_segments)] != base_segments:
            raise web.HTTPNotFound()
        segments = segments[len(base_segments) :]
    return segments


async def _run_cli_command(command_parts):
    command = [sys.executable, "-m", "shifter"] + command_parts
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    output = stdout.decode().strip() + "\n" + stderr.decode().strip()
    return process.returncode, output.strip()


async def _handle_form_action(request: web.Request, redirect_path: str = "/configure"):
    post_data = await request.post()
    session = await get_session(request)

    segments = list(_strip_base_path(request))
    if len(segments) < 2:
        raise web.HTTPBadRequest()
    service, action = segments[0], segments[1]

    command = [service, action]
    for key, value in post_data.items():
        if value:
            command.append(f"--{key.replace('_', '-')}")
            command.append(str(value))

    return_code, output = await _run_cli_command(command)
    message_type = "success" if return_code == 0 else "error"
    session["flash"] = {"type": message_type, "message": output}

    raise web.HTTPFound(_with_base_path(request.app, redirect_path))


@aiohttp_jinja2.template("index.html")
async def dashboard(request: web.Request):
    status_data = status_module.get_all_services_status()
    return {
        "services": status_data,
        "request": request,
        "base_path": request.app["base_path"],
        "base_path_prefix": request.app["base_path_prefix"],
    }


@aiohttp_jinja2.template("configure.html")
async def configure_page(request: web.Request):
    session = await get_session(request)
    flash_message = session.pop("flash", None)

    status_data = status_module.get_all_services_status()
    removable_items = {
        "gost": gost.list_rules(),
        "xray": xray.list_inbounds(),
        "haproxy": haproxy.list_tunnels(),
    }

    return {
        "flash": flash_message,
        "services": status_data,
        "removable_items": removable_items,
        "request": request,
        "base_path": request.app["base_path"],
        "base_path_prefix": request.app["base_path_prefix"],
    }


async def gost_install_action(request: web.Request):
    return await _handle_form_action(request)


async def gost_add_action(request: web.Request):
    return await _handle_form_action(request)


async def gost_remove_action(request: web.Request):
    return await _handle_form_action(request)


async def gost_uninstall_action(request: web.Request):
    return await _handle_form_action(request)


async def haproxy_install_action(request: web.Request):
    return await _handle_form_action(request)


async def haproxy_add_action(request: web.Request):
    return await _handle_form_action(request)


async def haproxy_remove_action(request: web.Request):
    return await _handle_form_action(request)


async def haproxy_uninstall_action(request: web.Request):
    return await _handle_form_action(request)


async def xray_install_action(request: web.Request):
    return await _handle_form_action(request)


async def xray_add_action(request: web.Request):
    return await _handle_form_action(request)


async def xray_remove_action(request: web.Request):
    return await _handle_form_action(request)


async def xray_uninstall_action(request: web.Request):
    return await _handle_form_action(request)


async def iptables_install_action(request: web.Request):
    return await _handle_form_action(request)


async def iptables_uninstall_action(request: web.Request):
    return await _handle_form_action(request)


def setup_routes(app: web.Application, base_path: str = "/") -> None:
    prefix = "" if base_path in ("", "/") else base_path.rstrip("/")

    def route_path(path: str) -> str:
        if path == "/":
            return prefix or "/"
        return f"{prefix}{path}"

    root_route = route_path("/")
    configure_route = route_path("/configure")

    app.router.add_get(root_route, dashboard)
    if root_route != "/" and not root_route.endswith("/"):
        app.router.add_get(f"{root_route}/", dashboard)

    app.router.add_get(configure_route, configure_page)
    if configure_route != "/" and not configure_route.endswith("/"):
        app.router.add_get(f"{configure_route}/", configure_page)

    app.router.add_post(route_path("/gost/install"), gost_install_action)
    app.router.add_post(route_path("/gost/add"), gost_add_action)
    app.router.add_post(route_path("/gost/remove"), gost_remove_action)
    app.router.add_post(route_path("/gost/uninstall"), gost_uninstall_action)

    app.router.add_post(route_path("/haproxy/install"), haproxy_install_action)
    app.router.add_post(route_path("/haproxy/add"), haproxy_add_action)
    app.router.add_post(route_path("/haproxy/remove"), haproxy_remove_action)
    app.router.add_post(route_path("/haproxy/uninstall"), haproxy_uninstall_action)

    app.router.add_post(route_path("/xray/install"), xray_install_action)
    app.router.add_post(route_path("/xray/add"), xray_add_action)
    app.router.add_post(route_path("/xray/remove"), xray_remove_action)
    app.router.add_post(route_path("/xray/uninstall"), xray_uninstall_action)

    app.router.add_post(route_path("/iptables/install"), iptables_install_action)
    app.router.add_post(route_path("/iptables/uninstall"), iptables_uninstall_action)
