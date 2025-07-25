from flask import Blueprint, jsonify, render_template
from mcstatus import JavaServer
from datetime import datetime
import asyncio

routes = Blueprint('routes', __name__)

STATUS_TIMEOUT = 3
QUERY_TIMEOUT = 2

from functools import wraps
def async_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

async def check_server(server_ip):
    start_time = datetime.now()
    try:
        try:
            server = await JavaServer.async_lookup(server_ip, timeout=STATUS_TIMEOUT)
            status = await server.async_status()
            basic_response = {
                "online": True,
                "ip": server.address,
                "version": status.version.name,
                "players": status.players.online,
                "max_players": status.players.max,
                "motd": str(status.description),
                "latency": status.latency,
                "last_updated": datetime.now().isoformat(),
                "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
            }
            if status.players.online > 0:
                asyncio.create_task(get_players_async(server_ip, basic_response))
            return basic_response
        except Exception as e:
            return {
                "online": False, 
                "error": str(e),
                "last_updated": datetime.now().isoformat(),
                "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }
    except Exception as e:
        return {
            "online": False, 
            "error": str(e),
            "last_updated": datetime.now().isoformat(),
            "response_time_ms": (datetime.now() - start_time).total_seconds() * 1000
        }

async def get_players_async(server_ip, basic_response):
    try:
        server = await JavaServer.async_lookup(server_ip, timeout=QUERY_TIMEOUT)
        query = await server.async_query()
        basic_response["players_list"] = query.players.names
        basic_response["player_query_completed"] = True
    except:
        basic_response["player_query_completed"] = False

@routes.route('/')
def home():
    return render_template('index.html')

@routes.route('/api/v1/status/<server_ip>')
@async_route
async def server_status(server_ip):
    result = await check_server(server_ip)
    return jsonify(result)