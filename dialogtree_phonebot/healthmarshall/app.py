from starlette.responses import Response
from fastapi import FastAPI, Request, Depends
from starlette.background import BackgroundTask
from starlette.config import Config
from starlette.staticfiles import StaticFiles
import os, logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .get_meds import get_meds
from typing_extensions import Annotated
from apptypes import AnnotatedDocument

config = Config(".env")
username = config('USERNAME')
password = config('PASSWORD')





app = FastAPI()
@app.post('/process-doc')
def process_doc(doc:str, patient:str) ->AnnotatedDocument:
    return get_meds.get_meds(doc, patient)

logger = logging.getLogger("gateway")
app.mount("/dist", StaticFiles(directory="frontend/dist"), name="dist")
app.mount("/discharge-instructions", StaticFiles(directory="discharge_instructions"), name="discharge-instructions")
app.mount("", StaticFiles(directory="frontend/public"), name="public")
 










    
    


