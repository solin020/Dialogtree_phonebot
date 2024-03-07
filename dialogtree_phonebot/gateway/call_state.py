import asyncio, aiofiles, os
from .conversation_controller import ConversationController
from ..config import (org_id,openai_key, call_recordings_directory)
from tempfile import NamedTemporaryFile
from dataclasses import dataclass
from ..dialogtree.dialog import Dialog


STOPWORD_LIST =  ["yes", "sure", "yep", "yeah", "go", "ahead", "next", "ready", "ok", "okay", "continue", "going"]
NEGATIVE_STOPWORD_LIST =  ["no", "nope", "not", "isn't", "don't", "nuh", "aren't", "aint", "wait", "yet", "bit"]


@dataclass
class CallState:
    call_sid: str
    phone_number: str
    history: list
    controller: ConversationController
    previous_calls: int
    uuid: str
    outbound_call_script: str
    inbound_call_script: str

    def __init__(self, 
                call_sid: str, 
                phone_number: str, 
                outbound_xml:str, 
                inbound_xml:str,
                controller):
        self.call_sid = call_sid
        self.phone_number = phone_number
        self.outbound_xml = outbound_xml
        self.inbound_xml = inbound_xml
        self.history = []
        self.controller = controller

    async def hangup_on_time_limit(self):
        await asyncio.sleep(600)
        await self.controller.goodbye()

    async def manage_call(self, inbound_or_outbound):
        match inbound_or_outbound:
            case "inbound": script_coro = self.inbound_coro()
            case "outbound": script_coro = self.outbound_coro()
        timer = asyncio.ensure_future(self.hangup_on_time_limit())
        script = asyncio.ensure_future(script_coro)
        await self.controller.end_event.wait()
        script.cancel()
        timer.cancel()
        print(f'call {self.call_sid} completed')


    async def say(self, quote:str, **kwargs):
        self.history.append(("SYSTEM", quote))
        await self.controller.say(quote=quote, **kwargs)

    async def ask(self, quote, **kwargs):
        self.history.append(("SYSTEM", quote))
        print('got to ask')
        reply =  await self.controller.ask(quote, **kwargs)
        self.history.append(("USER", reply))
        return reply
    
    def goodbye(self):
        self.controller.goodbye()
        
    async def outbound_coro(self):
        dialog = Dialog(conversation=self, 
                        treefile=self.outbound_xml, 
                        openai_key=openai_key, org_id=org_id, model="gpt-4", functions={})
        await dialog.start()

    async def inbound_coro(self):
        dialog = Dialog(conversation=self, 
                        treefile=self.inbound_xml, 
                        openai_key=openai_key, org_id=org_id, model="gpt-4", functions={})
        await dialog.start()





   

   


        
