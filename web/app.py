import os
import aiohttp_jinja2
import jinja2
from aiohttp import web
from .routes import routes

def create_app():
    """
    Creates and configures the aiohttp web application instance.
    """
    app = web.Application()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(os.path.join(base_dir, 'templates'))
    )
    
    app.add_routes(routes)
    
    app.router.add_static(
        '/static/',
        path=os.path.join(base_dir, 'static'),
        name='static'
    )
    
    return app