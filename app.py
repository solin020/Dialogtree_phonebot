from starlette.responses import Response
from fastapi import FastAPI, Request, Depends
from starlette.background import BackgroundTask
from starlette.config import Config
from starlette.staticfiles import StaticFiles
from twilio.twiml.voice_response import VoiceResponse, Connect
import os, logging
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from call_state import CallState, wss_url
from database import Session, CallLog as SqlCallLog, CallData
from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from authlib.integrations.starlette_client import OAuth
oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

config = Config(".env")
username = config('USERNAME')
password = config('PASSWORD')


app = FastAPI(root_path="/phonebot")
security = HTTPBasic()
async def verify_username(request: Request) -> HTTPBasicCredentials:

    credentials = await security(request)

    correct_username = secrets.compare_digest(credentials.username, username)
    correct_password = secrets.compare_digest(credentials.password, password)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

logger = logging.getLogger("gateway")
config = Config(".env")








call_dict = {}


@app.post('/stream-conversation', dependencies=[Depends(verify_username)])
async def stream_conversation(request:Request):

    task = BackgroundTask(begin_stream_conversation, (await request.form())['number'])
    
    return Response('OK', media_type='text/plain', background=task)

async def begin_stream_conversation(number):
    call =  CallState.outbound_call(number)
    call_dict[call.call_sid] = call


@app.route('/stream-conversation-receive', methods=['POST',])
async def stream_conversation_receive(request):
    form = await request.form()
    call_sid = form['CallSid']
    call_dict[call_sid] = CallState.inbound_call(form)
    vr = VoiceResponse()
    connect = Connect()
    connect.stream(url=f'{wss_url}/stream-conversation-socket')
    vr.append(connect)
    return Response(vr.__str__(), media_type='application/xml')

@app.websocket_route('/stream-conversation-socket')
async def stream_conversation_socket(websocket):
    print('websocket recieved')
    await websocket.accept()
    try:
        recording_bytes = bytearray()
        while True:
            frame = await websocket.receive_json()
            if frame['event'] == 'connected':
                print('connection accepted by stream_conversation', flush=True)
            elif frame['event'] == 'start':
                stream_sid = frame['start']['streamSid']
                call_sid = frame['start']['callSid']
            elif frame['event'] == 'media':
                await call_dict[call_sid].handle_streams(frame, websocket, stream_sid)
            elif frame['event'] == 'stop':
                print('starting close')
                await websocket.close()
                await call_dict[call_sid].after_call()
                call_dict.pop(call_sid)
                print('connection closed gracefully', flush=True)
                break
    except (WebSocketDisconnect, ConnectionClosedError,ConnectionClosedOK):
        await call_dict[call_sid].after_call()
        call_dict.pop(call_sid)
        print('connection closed disgracefully', flush=True)



class CallLog(BaseModel):
    call_sid:str
    data:CallData
    timestamp:str

@app.get('/api/call-log/{call_sid}', response_model=CallLog, dependencies=[Depends(verify_username)])
async def api_call_log(call_sid:str):
    session = Session()
    c = session.query(SqlCallLog).filter(SqlCallLog.call_sid == call_sid).one()
    return {k:(v if not v != v else 0) for (k, v) in {
            "call_sid":c.call_sid, 
            "data":c.data, 
            "timestamp":c.timestamp.isoformat(),
    }.items()}

class CallLogHeader(BaseModel):
    mturk_id: int
    call_sid:str
    timestamp: str

@app.get('/api/call-list', response_model=list[CallLog], dependencies=[Depends(verify_username)])
async def api_call_list():
    session = Session()
    return [{
            "mturk_id":call.data['mturk_id'], 
            "timestamp":call.data.timestamp.isoformat()
            } 
        for call
        in session.query(SqlCallLog)
    ]

if not os.path.exists('recordings'):
    os.mkdir('recordings')





    class AuthStaticFiles(StaticFiles):
        def __init__(self, *args, **kwargs) -> None:

            super().__init__(*args, **kwargs)

        async def __call__(self, scope, receive, send) -> None:

            assert scope["type"] == "http"

            request = Request(scope, receive)
            await verify_username(request)
            await super().__call__(scope, receive, send)


    app.mount("dist", AuthStaticFiles(directory="frontend/dist"), name="dist")
    app.mount("recordings", AuthStaticFiles(directory="calldb/recordings"), name="recordings")
    app.mount("", AuthStaticFiles(directory="frontend/public"), name="public")
 


