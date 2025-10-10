import os
import base64
import aiohttp_jinja2
import jinja2
from aiohttp import web
from aiohttp_session import setup, get_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from .routes import routes

def create_app():
    """
    Creates and configures the aiohttp web application instance.
    """
    app = web.Application()
    
    # Generate a new secret key every time the app starts, or use a persistent one from env vars
    secret_key = os.environ.get("AIOHTTP_SECRET_KEY", "").encode('utf-8')
    if not secret_key:
        secret_key = base64.urlsafe_b64decode(base64.urlsafe_b64encode(os.urandom(32)))

    setup(app, EncryptedCookieStorage(secret_key))
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(os.path.join(base_dir, 'templates'))
    )
    
    app.add_routes(routes)

    return app