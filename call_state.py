from twilio.twiml.voice_response import VoiceResponse, Connect
from twilio.rest import Client
from starlette.config import Config
import numpy as np
import asyncio, aiohttp, aiofiles, os
from functools import cached_property
import numpy as np, base64
from conversation_controller import ConversationController
config = Config(".env")
username = config('USERNAME')
password = config('PASSWORD')
account_sid = config('ACCOUNTSID')
auth_token = config('AUTHTOKEN')
client = Client(account_sid, auth_token)
import random
from num2words import num2words
from datetime import datetime
from database import Session, CallLog
STOPWORD_LIST =  ["yes", "sure", "yep", "yeah", "go", "go ahead", "next", "ready", "ok", "okay"]

public_url = "https://phonebot.rxinformatics.net"
wss_url = "wss://phonebot.rxinformatics.net"
llm_url = "http://localhost:5003"
MEMORY_WORDS = os.listdir('soundfiles')


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
        return "ffmpeg -i temp.wav -ar 8000 -f mulaw -acodec pcm_mulaw output.raw"
    

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








class CallState:
    def __init__(self):
        self.questions = []
        self.timestamp = datetime.now()
        self.controller = PhoneConversationController()
        self.memory_exercise_words=""
        self.memory_exercise_reply=""
        self.memory_grade=float("nan")
        self.memory_exercise_reply_2=""
        self.memory_grade_2=float("nan")
        self.f_reply=""
        self.f_grade=float("nan")
        self.animal_reply=""
        self.animal_grade=float("nan")

    async def after_call(self):
        print(f'call {self.call_sid} completed')
        async with aiofiles.open('internal.pcm', 'wb+') as f:
            await f.write(self.controller.internal_bytes)
        async with aiofiles.open('outbound.pcm', 'wb+') as f:
            await f.write(self.controller.outbound_bytes)
        proc = await asyncio.create_subprocess_shell(
            ('ffmpeg -ar 8k -f mulaw -i outbound.pcm -ar 16k -f s16le -i internal.pcm'
            ' -filter_complex "[0:a][1:a]join=inputs=2:channel_layout=stereo[a]" -map "[a]" '
            f'recordings/bot_{self.call_sid}.mp3'
            '&& rm internal.pcm outbound.pcm'),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        print(await proc.communicate(), flush=True)
        session = Session()
        session.add(CallLog(
            call_sid=self.call_sid, 
            data={
                "mturk_id":self.mturk_id,
                "conversation_log": self.controller.conversation_log,
            }, 
            timestamp=self.timestamp.isoformat(),
            
        ))
        session.commit()
        client.calls(self.call_sid).update(status='completed')
        

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

    def begin_conversation(self):
        vr = VoiceResponse()
        connect = Connect()
        connect.stream(url=f'{wss_url}/stream-conversation-socket')
        vr.append(connect)
        return vr




    @staticmethod
    def outbound_call(number):
        self = CallState()
        self.number = number
        vr = self.begin_conversation()
        call = client.calls.create(
            to='='+str(number),
            from_='+16122554456',
            twiml = vr.__str__(),
            status_callback_event=['answered',],
            status_callback_method='POST',
            status_callback = f"{public_url}/call-status",
        )
        self.call_sid = call.sid
        self.script = asyncio.ensure_future(self.patient_initiated_script())
        return self

    @staticmethod
    def inbound_call(form):
        self = CallState()
        self.call_sid = form['CallSid']
        self.number = int(form['From'])
        self.script = asyncio.ensure_future(self.bot_initiated_script())
        return self



 #    
        
   
    async def bot_initiated_script(self):
    #await self.controller.say("Hello. I am an automated nursing assistant with the salsa study.")
        await self.controller.say("This call will be recorded for research use")
        await self.controller.say("Because I am a robot, I can be slow sometimes. Please don't hang up if I take too long to respond or say things that don't make much sense.")
        mturk_id = random.randint(101,999)
        self.mturk_id = mturk_id
        words = ' '.join(num2words(mturk_id).split('-'))
        print("mturk_id", mturk_id)
        mturk_line = f"Your mechanical turk number for the user experience survey is {words}. Please write this number down to enter it in the survey later: {words}."
        print("line", mturk_line)
        await self.controller.say(mturk_line)
        response = await self.controller.ask("I am going to ask you a few questions. "
                     "Please listen carefully and answer them in as much detail as you can. "
                     "Are you ready?", stopword_list=STOPWORD_LIST)
        history = []
        init_question = ("Okay. First, I would like to ask you how you are feeling. "
                                "For example, have there been any changes in how you feel in the last few hours?")
        history.append(("SYSTEM", init_question))
        free_response_1 = await self.controller.ask(init_question,
                                minimum_turn_time=4,
                                await_silence=True,
                                silence_window=1)
        history.append(("USER", free_response_1))
        init_followup = await self.get_response(history)
        history.append(("SYSTEM", init_followup))
        free_response_2 = await(self.controller.ask(init_followup, await_silence=True, minimum_turn_time=10))
        history.append(("USER", free_response_2))
        #This gets a custom reply from the chatbot.
        topic = random.choice(["your favorite book", "your most memorable trip", "a memorable event in your life"])
        topic_question = (f"Thank you for sharing. Now, I would like to ask you to tell me as much as you can about {topic}. "
                                "Feel free to take your time in answering.")
        history.append(("SYSTEM", topic_question))
        free_response_3 = await self.controller.ask(f"Thank you for sharing. Now, I would like to ask you to tell me as much as you can about {topic}. "
                                "Feel free to take your time in answering.",
                                minimum_turn_time=4,
                                await_silence=True,
                                silence_window=1,
                                stopword_list=['please continue'])
        history.append(("USER", free_response_3))
        topic_followup = await self.get_response(history)
        history.append(("SYSTEM", topic_followup))
        free_response_4 = await(self.controller.ask(topic_followup, await_silence=True, minimum_turn_time=10, silence_window=4))  #This gets a custom reply from the chatbot.
        history.append(("USER", free_response_4))
        #async def perplexity_grade():
        #   async with aiohttp.ClientSession() as session:
        #       async with session.get(f'{llm_url}/perplexity', json=history) as resp:
        #           self.perplexity = await resp.json()
        #           print(gpt_perplexity)
        #perplexity_grade_handle = asyncio.ensure_future(perplexity_grade())
        response = await self.controller.ask("Thank you. Now, I am going to ask you to read a list of six words. "
                                "you will hear six words being spoken to you. Please repeat each word aloud as it is being spoken to you."
                                "Later, I will ask you to recall all six words. "
                                "Are you ready?",
                                stopword_list=STOPWORD_LIST)
        await self.controller.say("Here is the list. ",final_pause=1)
        self.word_files = random.choices(MEMORY_WORDS, k=6)
        self.memory_exercise_words = [w.split('.')[0] for w in self.word_files]
        for w in self.word_files:
          await self.controller.say(f'soundfiles/{w}', final_pause=1, file_=True)
        memory_response = await self.controller.ask("Say next when you are done",
                               wait_time=30, stopword_list=['next'])
        #async def memory_grade():
        #    async with aiohttp.ClientSession() as session:
        #        async with session.get('http://coherence:8000/grade-memory-test', json={
        #                'transcript': memory_response,
        #                'word_list': self.memory_exercise_words
        #            }) as resp:
        #            self.memory_grade = await resp.json()
        #            print(self.memory_grade)
        #memory_grade_handle = asyncio.ensure_future(memory_grade())
        response = await self.controller.ask("Thank you. Now, I will give you a letter of the alphabet. "
                               "I am going to ask you to name words that begin with that letter, as fast as you can. "
                               "For example, if I give you the letter S, as in sam, you can say soft, smile, and so on. "
                               "Do not use the same word with a different ending such as smiling, or smiles. "
                               "Are you ready?", stopword_list=STOPWORD_LIST)
        await self.controller.say("Okay. Your letter is the letter F, as in foxtrot. Please name all the words that you can think of that begin with the letter F. ")
        f_response = await self.controller.ask("You have thirty seconds. Please begin.", wait_time=30, stopword_list=['next'])
        #async def f_grade():
        #    async with aiohttp.ClientSession() as session:
        #        async with session.get('http://coherence:8000/grade-f-test', json=f_response) as resp:
        #            self.f_grade = await resp.json()
        #            print("f grade", self.f_grade)
        #f_grade_handle = asyncio.ensure_future(f_grade())
        response = await self.controller.ask("Please stop. Now, I will give you a category. "
                         "I am going to ask you to name as fast as you can all the things that belong to that category. "
                         "For example, if I give you the category of articles of clothing, you can say shirt, or jacket, or pants, and so on. "
                         "Are you ready?", stopword_list=STOPWORD_LIST)
        animal_response = await self.controller.ask("Okay. Your category is animals. Begin naming as many animals as you can think of. You have thirty seconds.", wait_time=30, stopword_list=['next'])
        #async def animal_grade():
        #    async with aiohttp.ClientSession() as session:
        #        async with session.get('http://coherence:8000/grade-animal-test', json=animal_response) as resp:
        #            self.animal_grade = await resp.json()
        #            print(self.animal_grade)
        #animal_grade_handle = asyncio.ensure_future(animal_grade())

        response = await self.controller.ask("Please stop. We are almost done. Just one last thing. "
                         "A few minutes ago I read a list of six words to you. "
                         "Please try to recall as many of these words as you can and say them aloud as you remember them. "
                         "You have thirty seconds. Please begin.", wait_time=30, stopword_list=['next'])
        speech_interval = await self.controller.ask("Thank you. This concludes our session. Until next time. Goodbye", wait_time=1)
        #await asyncio.gather(perplexity_grade_handle, memory_grade_handle, f_grade_handle, animal_grade_handle)








    async def patient_initiated_script(self):
        await self.bot_initiated_script()
    



    async def get_response(self, history):
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{llm_url}/generate', json=history) as resp:
                bot_says = await resp.text()
        print('bot', bot_says, flush=True)
        return bot_says
   


   


        
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
