from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.routing import Route
import depth


async def main(request):
    doc = await request.json()
    
    return JSONResponse(depth.main({'doc': str(doc)}, []))

app = Starlette(routes=[Route('/', main, methods=['POST'])])
