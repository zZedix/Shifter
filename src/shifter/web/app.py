import os
import base64

import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from .routes import setup_routes


def _normalize_base_path(base_path: str) -> str:
    cleaned = base_path.strip()
    if not cleaned:
        return "/"
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    cleaned = "/" + cleaned.strip("/")
    return "/" if cleaned == "//" else cleaned


def create_app(base_path: str = "/"):
    """
    Creates and configures the aiohttp web application instance.
    """
    normalized_base_path = _normalize_base_path(base_path)
    app = web.Application()

    secret_key = os.environ.get("AIOHTTP_SECRET_KEY", "").encode("utf-8")
    if not secret_key:
        secret_key = base64.urlsafe_b64decode(base64.urlsafe_b64encode(os.urandom(32)))

    setup(app, EncryptedCookieStorage(secret_key))

    base_dir = os.path.dirname(os.path.abspath(__file__))
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(os.path.join(base_dir, "templates")),
    )

    app["base_path"] = normalized_base_path
    app["base_path_prefix"] = "" if normalized_base_path == "/" else normalized_base_path

    setup_routes(app, base_path=normalized_base_path)

    if normalized_base_path != "/":
        async def not_found_root(_request):
            raise web.HTTPNotFound()

        app.router.add_route("*", "/", not_found_root)

    return app
