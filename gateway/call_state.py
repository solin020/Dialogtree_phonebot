from twilio.twiml.voice_response import VoiceResponse, Connect
from twilio.rest import Client
import numpy as np
import asyncio, aiohttp
from functools import cached_property
import numpy as np, base64
from .conversation_controller import ConversationController
from ..config import ( wss_url,
    account_sid, auth_token,org_id,openai_key, 
    sounds_directory, twilio_phone_number)
import os
from dataclasses import dataclass
from ..dialogtree.dialog import Dialog

client = Client(account_sid, auth_token)
STOPWORD_LIST =  ["yes", "sure", "yep", "yeah", "go", "ahead", "next", "ready", "ok", "okay", "continue", "going"]
NEGATIVE_STOPWORD_LIST =  ["no", "nope", "not", "isn't", "don't", "nuh", "aren't", "aint", "wait", "yet", "bit"]

phonebot_lock = asyncio.Lock()




class PhoneConversationController(ConversationController):
    def convert_to_16khz(self, bytes_):
        b = mulaw_decode_array[
                np.frombuffer(
                    bytes_, dtype='u1'
                )
            ].tobytes()
        blen = len(b)
        #the below line interpolates short 0s into the bytes and then gets the fourier transform of that
        ft = np.fft.fft(np.frombuffer((np.frombuffer(b, '<i2').astype('<i4') << 16).tobytes(), '<i2'))
        #this clears the high frequencies of the fourier tranform
        ft[blen // 2 - blen // 4 : blen // 2 + blen // 4] = 0
        #inverse fft returns the upsampled signal
        return np.fft.ifft(ft).astype('<i2').tobytes()

    @cached_property
    def ffmpeg_convert_to_outbound(self):
        return f"ffmpeg -i {self.temp_file} -ar 8000 -f mulaw -acodec pcm_mulaw {self.output_file}"
    

    @cached_property
    def INBOUND_SAMPLE_RATE(self):
        return 8000

    @cached_property
    def INBOUND_BYTE_WIDTH(self):
        return 1

    @cached_property
    def OUTBOUND_SAMPLE_RATE(self):
        return 8000

    @cached_property
    def OUTBOUND_BYTE_WIDTH(self):
        return 1

    @cached_property
    def OUTBOUND_ZERO_BYTE(self):
        return b'\x7f'



@dataclass
class CallLog:
    history:dict



@dataclass
class CallState:
    call_sid: str
    phone_number: str
    call_log: CallLog
    controller: ConversationController
    previous_calls: int
    uuid: str
    outbound_call_script: str
    inbound_call_script: str

    def __init__(self, call_sid: str, phone_number: str, outbound_call_script:str, inbound_call_script:str):
        self.call_sid = call_sid
        self.phone_number = phone_number
        self.outbound_call_script = outbound_call_script
        self.inbound_call_script = inbound_call_script
        self.call_log = CallLog(history=[])
        self.end_event = asyncio.Event()
        self.controller = PhoneConversationController()

    async def try_end(self):
        if phonebot_lock.locked():
            phonebot_lock.release()
        self.end_event.set()

    async def time_end(self):
        await asyncio.sleep(600)
        if phonebot_lock.locked():
            phonebot_lock.release()
        self.end_event.set()

    async def after_call(self, script):
        timer =asyncio.ensure_future(self.time_end())
        script = asyncio.ensure_future(script)
        await self.end_event.wait()
        print('ended early')
        script.cancel()
        timer.cancel()
        client.calls(self.call_sid).update(status='completed')
        print(f'call {self.call_sid} completed')



    async def handle_streams(self, frame, websocket, stream_sid):
        await self.controller.receive_inbound(base64.b64decode(frame['media']['payload']))
        inbytes = self.controller.get_speech_bytes()
        if inbytes:
            media_data = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                   "payload": base64.b64encode(inbytes).decode('utf-8')
                }
            }
            await websocket.send_json(media_data)

    @staticmethod
    def begin_conversation():
        vr = VoiceResponse()
        connect = Connect()
        connect.stream(url=f'{wss_url}/stream-conversation-socket')
        vr.append(connect)
        return vr




    @staticmethod
    async def outbound_call(phone_number: str):
        await phonebot_lock.acquire()
        call = client.calls.create(
            to='='+phone_number,
            from_=twilio_phone_number,
            twiml = CallState.begin_conversation().__str__(),
        )
        if call.sid:
            self = CallState(phone_number=phone_number,call_sid=call.sid)
            script = self.participant_initiated_script()
            asyncio.ensure_future(self.after_call(script))
            return self
        else:
            raise Exception("Twilio failure")

    @staticmethod
    async def inbound_call(form):
        await phonebot_lock.acquire()
        call_sid = form['CallSid']
        phone_number = form['From']
        self = CallState(call_sid=call_sid, phone_number=phone_number, 
                         outbound_call_script='/home/solin020/dialogtree_phonebot/dialogtree_phonebot/example.xml', 
                         inbound_call_script='/home/solin020/dialogtree_phonebot/dialogtree_phonebot/example.xml')
        script = self.bot_initiated_script()
        asyncio.ensure_future(self.after_call(script))
        return self
    
    async def say(self, quote:str, **kwargs):
        self.call_log.history.append(("SYSTEM", quote))
        await self.controller.say(quote=quote, **kwargs)

    async def ask(self, quote, **kwargs):
        self.call_log.history.append(("SYSTEM", quote))
        print('got to ask')
        reply =  await self.controller.ask(quote, **kwargs)
        self.call_log.history.append(("USER", reply))
        return reply
        
    








 #    
        
    #TODO: automate addition to history.
    async def bot_initiated_script(self):
        print('bot start')
        dialog = Dialog(conversation=self, treefile='/home/solin020/dialogtree_phonebot/dialogtree_phonebot/dialogtree/example.xml', 
                        openai_key=openai_key, org_id=org_id, model="gpt-4", functions={})
        await dialog.start()


    async def participant_initiated_script(self):
        dialog = Dialog(conversation=self, treefile='/home/solin020/dialogtree_phonebot/dialogtree_phonebot/dialogtree/example.xml', 
                        openai_key=openai_key, org_id=org_id, model="gpt-4", functions={})
        await dialog.start()


    async def ask_permission(self, quote):
        call_permission = await self.ask(quote, stopword_list=STOPWORD_LIST+NEGATIVE_STOPWORD_LIST, wait_time=30, return_stopword=True)
        print(f'{call_permission=}')
        if any(n in call_permission.lower() for n in NEGATIVE_STOPWORD_LIST) or not any(y in call_permission.lower() for y in STOPWORD_LIST):
            call_permission_2 = await self.ask("Okay. Say I'm ready when you're ready.", stopword_list=['ready'], wait_time=60)
            if not any(y in call_permission_2.lower() for y in STOPWORD_LIST):
                print('call again later')
                await self.controller.ask("Okay. Goodbye.", wait_time=1)
                client.calls(self.call_sid).update(status='completed')



   

class EndCall(Exception):
    pass

   


        
mulaw_decode_array = np.array(
      [-32124, -31100, -30076, -29052, -28028, -27004, -25980, -24956,
       -23932, -22908, -21884, -20860, -19836, -18812, -17788, -16764,
       -15996, -15484, -14972, -14460, -13948, -13436, -12924, -12412,
       -11900, -11388, -10876, -10364,  -9852,  -9340,  -8828,  -8316,
        -7932,  -7676,  -7420,  -7164,  -6908,  -6652,  -6396,  -6140,
        -5884,  -5628,  -5372,  -5116,  -4860,  -4604,  -4348,  -4092,
        -3900,  -3772,  -3644,  -3516,  -3388,  -3260,  -3132,  -3004,
        -2876,  -2748,  -2620,  -2492,  -2364,  -2236,  -2108,  -1980,
        -1884,  -1820,  -1756,  -1692,  -1628,  -1564,  -1500,  -1436,
        -1372,  -1308,  -1244,  -1180,  -1116,  -1052,   -988,   -924,
         -876,   -844,   -812,   -780,   -748,   -716,   -684,   -652,
         -620,   -588,   -556,   -524,   -492,   -460,   -428,   -396,
         -372,   -356,   -340,   -324,   -308,   -292,   -276,   -260,
         -244,   -228,   -212,   -196,   -180,   -164,   -148,   -132,
         -120,   -112,   -104,    -96,    -88,    -80,    -72,    -64,
          -56,    -48,    -40,    -32,    -24,    -16,     -8,      0,
        32124,  31100,  30076,  29052,  28028,  27004,  25980,  24956,
        23932,  22908,  21884,  20860,  19836,  18812,  17788,  16764,
        15996,  15484,  14972,  14460,  13948,  13436,  12924,  12412,
        11900,  11388,  10876,  10364,   9852,   9340,   8828,   8316,
         7932,   7676,   7420,   7164,   6908,   6652,   6396,   6140,
         5884,   5628,   5372,   5116,   4860,   4604,   4348,   4092,
         3900,   3772,   3644,   3516,   3388,   3260,   3132,   3004,
         2876,   2748,   2620,   2492,   2364,   2236,   2108,   1980,
         1884,   1820,   1756,   1692,   1628,   1564,   1500,   1436,
         1372,   1308,   1244,   1180,   1116,   1052,    988,    924,
          876,    844,    812,    780,    748,    716,    684,    652,
          620,    588,    556,    524,    492,    460,    428,    396,
          372,    356,    340,    324,    308,    292,    276,    260,
          244,    228,    212,    196,    180,    164,    148,    132,
          120,    112,    104,     96,     88,     80,     72,     64,
           56,     48,     40,     32,     24,     16,      8,      0] 
, dtype='<i2')
