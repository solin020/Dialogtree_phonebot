from starlette.responses import Response, FileResponse
from fastapi import FastAPI
from starlette.background import BackgroundTask
from twilio.twiml.voice_response import VoiceResponse, Connect
import os
from .call_state import CallState
from .phone_conversation_translator import PhoneConversationTranslator
from .browser_conversation_translator import BrowserConversationTranslator
from .conversation_controller import ConversationController
from ..config import (main_port, wss_url,
    account_sid, auth_token,org_id,openai_key, 
    sounds_directory, twilio_phone_number)
from twilio.rest import Client
client = Client(account_sid, auth_token)

import asyncio, uuid
dir_path = os.path.dirname(os.path.realpath(__file__))
phonebot_lock = asyncio.Lock()
inbound_or_outbound = None
this_phone_number = None

app = FastAPI()

my_xml = '/home/solin020/dialogtree_phonebot/dialogtree_phonebot/dialogtree/example.xml'


#region Twilio Logic


@app.route('/make-call', methods=['POST'])
async def make_call(request):
    phone_number = await request.json()
    task = BackgroundTask(begin_outbound_call, phone_number)
    return Response('OK', media_type='text/plain', background=task)

async def begin_outbound_call(phone_number):
    await phonebot_lock.acquire()
    global inbound_or_outbound, this_phone_number
    inbound_or_outbound = 'outbound'
    this_phone_number = phone_number
    client.calls.create(
            to='='+phone_number,
            from_=twilio_phone_number,
            twiml = CallState.begin_conversation().__str__(),
    )

@app.route('/stream-conversation-receive', methods=['POST',])
async def stream_conversation_receive(request):
    global this_phone_number, inbound_or_outbound
    vr = VoiceResponse()
    if phonebot_lock.locked():
        print('rejected because busy')
        vr.reject(reason='busy')
        return Response(vr.__str__(), media_type='application/xml')
    await phonebot_lock.acquire()
    inbound_or_outbound = 'inbound'
    form = await request.form()
    this_phone_number = form['From']
    connect = Connect()
    connect.stream(url=f'{wss_url}/stream-conversation-socket')
    vr.append(connect)
    return Response(vr.__str__(), media_type='application/xml')

@app.websocket_route('/stream-conversation-socket')
async def stream_conversation_socket(websocket):
    global inbound_or_outbound
    await websocket.accept()
    print('websocket recieved', flush=True)
    connected_frame = await websocket.receive_json()
    assert connected_frame['event'] == 'connected'
    print('connection accepted by stream_conversation', flush=True)
    started_frame = await websocket.receive_json()
    assert started_frame['event'] == 'start'
    stream_sid = started_frame['start']['streamSid']
    call_sid = started_frame['start']['callSid']
    controller = ConversationController()
    translator = PhoneConversationTranslator(
        controller=controller,
        websocket = websocket,
        call_sid=call_sid,
        stream_sid=stream_sid
    )
    call_state = CallState(
        call_sid=call_sid,
        phone_number=this_phone_number,
        outbound_xml=my_xml,
        inbound_xml=my_xml,
        controller=controller
    )
    asyncio.ensure_future(call_state.manage_call(inbound_or_outbound))
    await translator.handle_websocket(client, phonebot_lock)





@app.websocket_route('/browser-conversation-socket')
async def browser_conversation_socket(websocket):
    await websocket.accept()
    if phonebot_lock.locked():
        websocket.send_text("busy")
        websocket.close()
    await phonebot_lock.acquire()
    print('connection accepted by stream_conversation', flush=True)
    endian_code, sample_rate = (await websocket.receive_text()).split()
    sample_rate = int(sample_rate)
    conn_id = str(uuid.uuid4())
    controller = ConversationController()
    translator = BrowserConversationTranslator(
        websocket=websocket,
        controller=controller,
        sample_rate=sample_rate,
        endian_code=endian_code,
        call_sid=conn_id,
    )
    call_state = CallState(
        call_sid=conn_id,
        phone_number=conn_id,
        outbound_xml=my_xml,
        inbound_xml=my_xml,
        controller=controller
    )
    asyncio.ensure_future(call_state.manage_call("inbound"))
    await translator.handle_websocket(phonebot_lock)


@app.get('/index.html')
async def index_html():
    return FileResponse('dialogtree_phonebot/frontend/index.html')
    


@app.get('/receive-speaker.js')
async def f32_pcm_js():
    return FileResponse('dialogtree_phonebot/frontend/receive-speaker.js')

@app.get('/send-microphone.js')
async def f32_pcm_js():
    return FileResponse('dialogtree_phonebot/frontend/send-microphone.js')

#endregion
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=int(main_port))


