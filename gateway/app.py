from starlette.responses import Response
from fastapi import FastAPI
from starlette.background import BackgroundTask
from twilio.twiml.voice_response import VoiceResponse, Connect
import os
from starlette.websockets import WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from .call_state import CallState, wss_url
import base64
from ..config import main_port
dir_path = os.path.dirname(os.path.realpath(__file__))

app = FastAPI()


#region Twilio Logic
call_dict:dict[str,CallState] = {}

@app.route('/make-call', methods=['POST'])
async def make_call(request):
    phone_number, previous_rejects = await request.json()
    task = BackgroundTask(begin_stream_conversation, phone_number, int(previous_rejects))
    return Response('OK', media_type='text/plain', background=task)

async def begin_stream_conversation(number, previous_rejects):
    call =  await CallState.outbound_call(number, previous_rejects)
    call_dict[call.call_sid] = call

@app.route('/stream-conversation-receive', methods=['POST',])
async def stream_conversation_receive(request):
    from .call_state import phonebot_lock
    form = await request.form()
    vr = VoiceResponse()
    if not phonebot_lock.locked():
        call_sid = form['CallSid']
        call_dict[call_sid] = await CallState.inbound_call(form)
        connect = Connect()
        connect.stream(url=f'{wss_url}/stream-conversation-socket')
        vr.append(connect)
    else:
        vr.reject(reason='busy')
    return Response(vr.__str__(), media_type='application/xml')

@app.websocket_route('/stream-conversation-socket')
async def stream_conversation_socket(websocket):
    from .call_state import EndCall
    print('websocket recieved')
    await websocket.accept()
    call_sid = ""
    stream_sid = ""
    try:
        while True:
            frame = await websocket.receive_json()
            if frame['event'] == 'connected':
                print('connection accepted by stream_conversation', flush=True)
            elif frame['event'] == 'start':
                stream_sid = frame['start']['streamSid']
                call_sid = frame['start']['callSid']
            elif frame['event'] == 'media':
                if call_sid in call_dict:
                    call_state = call_dict[call_sid]
                    await call_state.handle_streams(frame, websocket, stream_sid)
                #This handles the case where the CallState object for this call hasn't been initialized yet
                else:
                    print('not recieved', call_sid)
                    recieved_bytes = base64.b64decode(frame['media']['payload'])
                    inbytes = b'\x7f' * len(recieved_bytes)
                    if inbytes:
                        media_data = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {
                            "payload": base64.b64encode(inbytes).decode('utf-8')
                            }
                        }
                        await websocket.send_json(media_data) 
            elif frame['event'] == 'stop':
                print('starting close')
                await websocket.close()
                print('connection closed gracefully', flush=True)
                break
    except (WebSocketDisconnect, ConnectionClosedError, ConnectionClosedOK):
        print('connection closed disgracefully', flush=True)
    except EndCall:
        print('call ended')
    finally:
        await call_dict[call_sid].try_end()
        call_dict.pop(call_sid)

#endregion
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=int(main_port))


