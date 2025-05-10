from aiohttp import web
import asyncio
import os

from modules.routes import setup_routes
from modules.clothes_processor import ClothesProcessor

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

pcs = set()
ml_model = ClothesProcessor()

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

def init_app():
    app = web.Application()
    
    setup_routes(app, pcs, ml_model, UPLOAD_DIR)
    
    app.router.add_static("/static/", path="./static", name="static")

    app.on_shutdown.append(on_shutdown)
    
    return app

if __name__ == "__main__":
    app = init_app()
    web.run_app(app, port=8080)