from fastapi.openapi.utils import get_openapi
from gateway.app import app
import json
from config import frontend_directory
import os


with open(os.path.join(frontend_directory,'openapi.json'), 'w') as f:
    json.dump(get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    ), f)
