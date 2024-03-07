
import numpy as np, asyncio
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from starlette.websockets import WebSocketDisconnect
from .conversation_controller import EndCall




class BrowserConversationTranslator:
    def __init__(self, websocket, sample_rate, endian_code, call_sid, controller):
        self.websocket = websocket
        self.controller = controller
        self.sample_rate = sample_rate
        self.endian_code = endian_code
        self.call_sid = call_sid
        self.inbytes = bytearray()
    
    async def handle_websocket(self, phonebot_lock):
        try:
            while True:
                bytes_ = await self.websocket.receive_bytes()
                await self.translate_receive_inbound(bytes_)
                await self.websocket.send_bytes(self.translate_send_outbound())
        except (WebSocketDisconnect, ConnectionClosedError, ConnectionClosedOK):
            print('connection closed disgracefully', flush=True)
        except EndCall:
            print('call ended')
        finally:
            self.controller.goodbye()
            phonebot_lock.release()
            with open('test.pcm', 'wb+') as f:
                f.write(self.inbytes)


    async def translate_receive_inbound(self, bytes_):
        self.inbytes.extend(bytes_)
        resample = 16000 / self.sample_rate
        code = '<f4' if self.endian_code=='le' else '>f4'
        y = np.frombuffer(bytes_, code) * 32768
        oldxlen = y.size
        oldx = np.linspace(0, oldxlen, oldxlen)
        newx = np.linspace(0, oldxlen, int(oldxlen*resample))
        newbytes = np.interp(newx, oldx, y).astype('<i2').tobytes()
        await self.controller.receive_inbound(newbytes)


    def translate_send_outbound(self):
        bytes_ = self.controller.send_outbound()
        resample = self.sample_rate/16000
        code = '<f4' if self.endian_code=='le' else '>f4'
        y = np.frombuffer(bytes_, '<i2')
        oldxlen = y.size
        oldx = np.linspace(0, oldxlen, oldxlen)
        newx = np.linspace(0, oldxlen, int(oldxlen*resample))
        return (np.interp(newx, oldx, y)/32768).astype(code).tobytes()
