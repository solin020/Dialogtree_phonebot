import numpy as np, base64, asyncio
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from starlette.websockets import WebSocketDisconnect
from mulaw import pcms16le_to_mulaw
from .conversation_controller import EndCall

class PhoneConversationTranslator:
    def __init__(self, controller, websocket, call_sid, stream_sid):
        self.controller = controller
        self.websocket = websocket 
        self.call_sid = call_sid
        self.stream_sid = stream_sid

    async def translate_receive_inbound(self, bytes_):
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
        await self.controller.receive_inbound(np.fft.ifft(ft).astype('<i2').tobytes())
    
    def translate_send_outbound(self):
        bytes_ = self.controller.send_outbound()
        return pcms16le_to_mulaw(bytes_)
    
    async def handle_websocket(self, client, phonebot_lock):
        try:
            while True:
                frame = await self.websocket.receive_json()
                if frame['event'] == 'media':
                    bytes_ = base64.b64decode(frame['media']['payload'])
                    await self.translate_receive_inbound(bytes_)
                    outbytes = self.translate_send_outbound()
                    media_data = {
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {
                            "payload": base64.b64encode(outbytes).decode('utf-8')
                        }
                    }
                    await self.websocket.send_json(media_data)
                elif frame['event'] == 'stop':
                    print('starting close')
                    await self.websocket.close()
                    print('connection closed gracefully', flush=True)
                    break
        except (WebSocketDisconnect, ConnectionClosedError, ConnectionClosedOK):
            print('connection closed disgracefully', flush=True)
        except EndCall:
            client.calls(self.call_sid).update(status='completed')
            print('call ended')
        finally:
            self.controller.goodbye()
            phonebot_lock.release()





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
