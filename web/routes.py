import sys
import asyncio
from aiohttp import web
import aiohttp_jinja2
from urllib.parse import quote, unquote

from scripts import status as status_module
from scripts import gost, xray, haproxy, iptables

routes = web.RouteTableDef()

async def _run_cli_command(command_parts):
    """
    Runs a shifter CLI command as a subprocess and captures its output.
    This is the bridge between the web UI and the core CLI logic.
    """
    command = [sys.executable, 'cli.py'] + command_parts
    
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    output = stdout.decode().strip() + "\n" + stderr.decode().strip()
    return process.returncode, output.strip()

async def _handle_form_action(request, redirect_url='/configure'):
    """
    A generic handler for form submissions that call the CLI.
    """
    post_data = await request.post()
    
    path_parts = request.path.strip('/').split('/')
    service, action = path_parts[0], path_parts[1]

    command = [service, action]
    for key, value in post_data.items():
        if value:
            command.append(f'--{key.replace("_", "-")}')
            command.append(str(value))

    return_code, output = await _run_cli_command(command)
    
    message_type = 'success' if return_code == 0 else 'error'
    
    location = f"{redirect_url}?message={quote(output)}&type={message_type}"
    raise web.HTTPFound(location)


@routes.get('/')
@aiohttp_jinja2.template('index.html')
async def dashboard(request):
    """Renders the main dashboard page."""
    status_data = status_module.get_all_services_status()
    return {'services': status_data}

@routes.get('/configure')
@aiohttp_jinja2.template('configure.html')
async def configure_page(request):
    """Renders the configuration page, passing status data and any flash messages."""
    message = request.query.get('message', '')
    message_type = request.query.get('type', 'info')
    
    status_data = status_module.get_all_services_status()
    
    removable_items = {
        'gost': gost.list_rules(),
        'xray': xray.list_inbounds(),
        'haproxy': haproxy.list_tunnels()
    }
    
    return {
        'message': unquote(message), 
        'message_type': message_type,
        'services': status_data,
        'removable_items': removable_items
    }

# --- Action Routes (POST) ---

# GOST Actions
@routes.post('/gost/install')
async def gost_install_action(request): return await _handle_form_action(request)
@routes.post('/gost/add')
async def gost_add_action(request): return await _handle_form_action(request)
@routes.post('/gost/remove')
async def gost_remove_action(request): return await _handle_form_action(request)
@routes.post('/gost/uninstall')
async def gost_uninstall_action(request): return await _handle_form_action(request)

# HAProxy Actions
@routes.post('/haproxy/install')
async def haproxy_install_action(request): return await _handle_form_action(request)
@routes.post('/haproxy/add')
async def haproxy_add_action(request): return await _handle_form_action(request)
@routes.post('/haproxy/remove')
async def haproxy_remove_action(request): return await _handle_form_action(request)
@routes.post('/haproxy/uninstall')
async def haproxy_uninstall_action(request): return await _handle_form_action(request)

# Xray Actions
@routes.post('/xray/install')
async def xray_install_action(request): return await _handle_form_action(request)
@routes.post('/xray/add')
async def xray_add_action(request): return await _handle_form_action(request)
@routes.post('/xray/remove')
async def xray_remove_action(request): return await _handle_form_action(request)
@routes.post('/xray/uninstall')
async def xray_uninstall_action(request): return await _handle_form_action(request)

# IPTables Actions
@routes.post('/iptables/install')
async def iptables_install_action(request): return await _handle_form_action(request)
@routes.post('/iptables/uninstall')
async def iptables_uninstall_action(request): return await _handle_form_action(request)