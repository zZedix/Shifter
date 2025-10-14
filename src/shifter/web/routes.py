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


def _login_path(request: web.Request) -> str:
    return _with_base_path(request.app, "/login")


async def _require_auth(request: web.Request):
    session = await get_session(request)
    if not session.get("user"):
        raise web.HTTPFound(_login_path(request))
    return session


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
    session = await _require_auth(request)

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
    session = await _require_auth(request)
    status_data = status_module.get_all_services_status()
    return {
        "services": status_data,
        "request": request,
        "base_path": request.app["base_path"],
        "base_path_prefix": request.app["base_path_prefix"],
        "user": session.get("user"),
    }


@aiohttp_jinja2.template("configure.html")
async def configure_page(request: web.Request):
    session = await _require_auth(request)
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
        "user": session.get("user"),
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


@aiohttp_jinja2.template("login.html")
async def login_page(request: web.Request):
    session = await get_session(request)
    if session.get("user"):
        raise web.HTTPFound(_with_base_path(request.app, "/"))
    flash_message = session.pop("flash", None)
    return {
        "flash": flash_message,
        "request": request,
        "base_path": request.app["base_path"],
        "base_path_prefix": request.app["base_path_prefix"],
        "user": None,
    }


async def login_action(request: web.Request):
    post_data = await request.post()
    username = post_data.get("username", "").strip()
    password = post_data.get("password", "")
    session = await get_session(request)
    auth_manager = request.app["auth_manager"]

    if username == auth_manager.username and auth_manager.verify_password(password):
        session["user"] = {"username": auth_manager.username}
        session["flash"] = {"type": "success", "message": "Logged in successfully."}
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    session["flash"] = {"type": "error", "message": "Invalid username or password."}
    raise web.HTTPFound(_with_base_path(request.app, "/login"))


async def logout_action(request: web.Request):
    session = await get_session(request)
    session.invalidate()
    session = await get_session(request)
    session["flash"] = {"type": "success", "message": "Signed out successfully."}
    raise web.HTTPFound(_with_base_path(request.app, "/login"))


async def change_credentials_action(request: web.Request):
    session = await _require_auth(request)
    post_data = await request.post()
    current_password = post_data.get("current_password", "")
    new_username = post_data.get("new_username", "").strip()
    new_password = post_data.get("new_password", "")
    confirm_password = post_data.get("confirm_password", "")

    auth_manager = request.app["auth_manager"]

    if not auth_manager.verify_password(current_password):
        session["flash"] = {"type": "error", "message": "Current password was incorrect."}
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    if not new_username:
        session["flash"] = {"type": "error", "message": "New username must not be empty."}
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    if not new_password:
        session["flash"] = {"type": "error", "message": "New password must not be empty."}
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    if new_password != confirm_password:
        session["flash"] = {"type": "error", "message": "New password confirmation does not match."}
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    if len(new_password) < 8:
        session["flash"] = {
            "type": "error",
            "message": "New password must be at least 8 characters long.",
        }
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    auth_manager.update_credentials(new_username, new_password)
    session["user"] = {"username": auth_manager.username}
    session["flash"] = {"type": "success", "message": "Credentials updated successfully."}
    raise web.HTTPFound(_with_base_path(request.app, "/configure"))


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

    login_route = route_path("/login")
    logout_route = route_path("/logout")
    change_credentials_route = route_path("/auth/change")

    app.router.add_get(login_route, login_page)
    app.router.add_post(login_route, login_action)
    app.router.add_post(logout_route, logout_action)
    app.router.add_post(change_credentials_route, change_credentials_action)

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


def _login_path(request: web.Request) -> str:
    return _with_base_path(request.app, "/login")


async def _require_auth(request: web.Request):
    session = await get_session(request)
    if not session.get("user"):
        raise web.HTTPFound(_login_path(request))
    return session


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
    session = await _require_auth(request)

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
    session = await _require_auth(request)
    status_data = status_module.get_all_services_status()
    return {
        "services": status_data,
        "request": request,
        "base_path": request.app["base_path"],
        "base_path_prefix": request.app["base_path_prefix"],
        "user": session.get("user"),
    }


@aiohttp_jinja2.template("configure.html")
async def configure_page(request: web.Request):
    session = await _require_auth(request)
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
        "user": session.get("user"),
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


@aiohttp_jinja2.template("login.html")
async def login_page(request: web.Request):
    session = await get_session(request)
    if session.get("user"):
        raise web.HTTPFound(_with_base_path(request.app, "/"))
    flash_message = session.pop("flash", None)
    return {
        "flash": flash_message,
        "request": request,
        "base_path": request.app["base_path"],
        "base_path_prefix": request.app["base_path_prefix"],
        "user": None,
    }


async def login_action(request: web.Request):
    post_data = await request.post()
    username = post_data.get("username", "").strip()
    password = post_data.get("password", "")
    session = await get_session(request)
    auth_manager = request.app["auth_manager"]

    if username == auth_manager.username and auth_manager.verify_password(password):
        session["user"] = {"username": auth_manager.username}
        session["flash"] = {"type": "success", "message": "Logged in successfully."}
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    session["flash"] = {"type": "error", "message": "Invalid username or password."}
    raise web.HTTPFound(_with_base_path(request.app, "/login"))


async def logout_action(request: web.Request):
    session = await get_session(request)
    session.invalidate()
    session = await get_session(request)
    session["flash"] = {"type": "success", "message": "Signed out successfully."}
    raise web.HTTPFound(_with_base_path(request.app, "/login"))


async def change_credentials_action(request: web.Request):
    session = await _require_auth(request)
    post_data = await request.post()
    current_password = post_data.get("current_password", "")
    new_username = post_data.get("new_username", "").strip()
    new_password = post_data.get("new_password", "")
    confirm_password = post_data.get("confirm_password", "")

    auth_manager = request.app["auth_manager"]

    if not auth_manager.verify_password(current_password):
        session["flash"] = {"type": "error", "message": "Current password was incorrect."}
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    if not new_username:
        session["flash"] = {"type": "error", "message": "New username must not be empty."}
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    if not new_password:
        session["flash"] = {"type": "error", "message": "New password must not be empty."}
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    if new_password != confirm_password:
        session["flash"] = {"type": "error", "message": "New password confirmation does not match."}
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    if len(new_password) < 8:
        session["flash"] = {
            "type": "error",
            "message": "New password must be at least 8 characters long.",
        }
        raise web.HTTPFound(_with_base_path(request.app, "/configure"))

    auth_manager.update_credentials(new_username, new_password)
    session["user"] = {"username": auth_manager.username}
    session["flash"] = {"type": "success", "message": "Credentials updated successfully."}
    raise web.HTTPFound(_with_base_path(request.app, "/configure"))


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

    login_route = route_path("/login")
    logout_route = route_path("/logout")
    change_credentials_route = route_path("/auth/change")

    app.router.add_get(login_route, login_page)
    app.router.add_post(login_route, login_action)
    app.router.add_post(logout_route, logout_action)
    app.router.add_post(change_credentials_route, change_credentials_action)

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
