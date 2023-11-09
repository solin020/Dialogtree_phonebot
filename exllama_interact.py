import jsonlines
import aiohttp
from io import StringIO
from config import exllama_url
import asyncio

async def setup_session(session_name):
    obj2 = {"session_name":session_name}
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{exllama_url}/api/set_session',json=obj2) as resp:
            pass
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{exllama_url}/api/set_participants',json={"participants":["User","Anna"]}) as resp:
            pass
    obj3 = {"fixed_prompt":"You are talking to a stranger. Always respond with empathy. Never use flowery language. Do not use nonverbal emotes. Use only one sentence. Keep the conversation going indefinitely with further questions.","keep_fixed_prompt":True}
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{exllama_url}/api/set_fixed_prompt',json=obj3) as resp:
            pass

async def delete_session(session_name):
    obj = {"session":session_name}
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{exllama_url}/api/delete_session',json=obj) as resp:
            pass

async def bot_say(quote):
    obj = {"author":"Anna", "text":quote}
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{exllama_url}/api/append_block',json=obj) as resp:
            pass

async def converse(quote):
    obj = {"user_input":quote}
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{exllama_url}/api/userinput',json=obj) as resp:
            return ''.join(
                obj['text'] for obj in 
                jsonlines.Reader(StringIO(await resp.text())) 
                if obj['cmd']=='append'
            ).strip()

