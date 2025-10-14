from __future__ import annotations

import os
import base64

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp_session import setup, get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from .routes import setup_routes
from .auth import AuthManager, AuthConfigError


def _normalize_base_path(base_path: str) -> str:
    cleaned = base_path.strip()
    if not cleaned:
        return "/"
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    cleaned = "/" + cleaned.strip("/")
    return "/" if cleaned == "//" else cleaned


def create_app(base_path: str = "/", auth_manager: AuthManager | None = None):
    """
    Creates and configures the aiohttp web application instance.
    """
    normalized_base_path = _normalize_base_path(base_path)
    app = web.Application()

    secret_key = os.environ.get("AIOHTTP_SECRET_KEY", "").encode("utf-8")
    if not secret_key:
        secret_key = base64.urlsafe_b64decode(base64.urlsafe_b64encode(os.urandom(32)))

    secure_cookie_env = os.environ.get("SHIFTER_SESSION_SECURE", "false").lower() in {"1", "true", "yes"}
    storage = EncryptedCookieStorage(
        secret_key,
        cookie_name="shifter_session",
        secure=secure_cookie_env,
        httponly=True,
    )
    setup(app, storage)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(os.path.join(base_dir, "templates")),
    )

    app["base_path"] = normalized_base_path
    app["base_path_prefix"] = "" if normalized_base_path == "/" else normalized_base_path

    try:
        manager = auth_manager or AuthManager()
    except AuthConfigError as exc:
        raise RuntimeError(str(exc)) from exc

    app["auth_manager"] = manager

    @web.middleware
    async def _session_user_middleware(request, handler):
        session = await get_session(request)
        request["user"] = session.get("user")
        return await handler(request)

    app.middlewares.append(_session_user_middleware)

    setup_routes(app, base_path=normalized_base_path)

    if normalized_base_path != "/":
        async def not_found_root(_request):
            raise web.HTTPNotFound()

        app.router.add_route("*", "/", not_found_root)

    return app
