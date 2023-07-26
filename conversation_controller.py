import asyncio, webrtcvad, aiohttp, aiofiles, collections
from functools import cached_property
from abc import ABC, abstractmethod

vad = webrtcvad.Vad()
vad.set_mode(1)
tts_lock = asyncio.Lock()

INTERNAL_SAMPLE_RATE=16000
INTERNAL_BYTE_WIDTH=2
VAD_FRAME_BYTES = INTERNAL_BYTE_WIDTH * int((INTERNAL_SAMPLE_RATE/100)*3)


def seconds_to_time(t):
    return INTERNAL_BYTE_WIDTH * int(t*INTERNAL_SAMPLE_RATE)

  
OUTBOUND_BUFFER = 600
SILENCE_THRESHOLD = 0.2
tts_url = "http://localhost:5001"
stt_url = "http://localhost:5002"
llm_url = "http://localhost:5003"


class ConversationController(ABC):
    def __init__(self):
        self.internal_bytes = bytearray()
        self.internal_pos = 0
        self.outbound_pos = 0
        self.vad_pos = 0
        self.outbound_bytes = bytearray()
        self.check_silence = False
        self.check_stopwords = False
        self.conversation_log = []
        self.timers = {}
        self.frames = bytearray()


    async def check_timers(self):
        evict_flags = []
        for k, v in self.timers.items():
            if self.outbound_pos > k:
                v.set()
                evict_flags.append(k)
        for k in evict_flags:
            self.timers.pop(k)


    def add_timer(self, end_pos):
        timer = asyncio.Event()
        self.timers[end_pos] = timer
        return timer

    @cached_property
    def outbound_over_internal(self):
        return ((self.OUTBOUND_SAMPLE_RATE*self.OUTBOUND_BYTE_WIDTH)/\
        (INTERNAL_SAMPLE_RATE*INTERNAL_BYTE_WIDTH))


    
    def get_speech_bytes(self):
        received_pos = int(len(self.internal_bytes) * self.outbound_over_internal)
        buffer_pos = received_pos + OUTBOUND_BUFFER
        silence_needed = buffer_pos - len(self.outbound_bytes)
        if silence_needed > 0:
            self.outbound_bytes.extend(silence_needed*self.OUTBOUND_ZERO_BYTE)
        retval = self.outbound_bytes[self.outbound_pos:buffer_pos]
        self.outbound_pos = buffer_pos
        return retval

    async def pause(self, seconds):
        self.outbound_bytes.extend(int(seconds_to_time(seconds) * self.outbound_over_internal) * self.OUTBOUND_ZERO_BYTE)


 
            
    async def listen(self):
        while len(self.internal_bytes) > (self.vad_pos + VAD_FRAME_BYTES):
            frame = self.internal_bytes[self.vad_pos:self.vad_pos + VAD_FRAME_BYTES]
            if self.check_silence:
                is_speech = vad.is_speech(frame, INTERNAL_SAMPLE_RATE)
                self.is_speech_queue.put_nowait(is_speech)
                if is_speech and self.check_stopwords:
                    self.frames.extend(frame)
                elif self.frames and self.check_stopwords:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(f'{stt_url}/process-bytes', data=self.frames) as resp:
                            stopword = await resp.text()
                            print('stopword', stopword, flush=True)
                            self.stopword_queue.put_nowait(stopword)
                            self.frames = bytearray()
            self.vad_pos += VAD_FRAME_BYTES

    async def await_silence(self, minimum_turn_time, silence_window=1):
        silence_window_vadframes = int(silence_window//0.03)
        await asyncio.sleep(minimum_turn_time)
        self.check_silence = True
        self.is_speech_queue = asyncio.Queue()
        observation_window = collections.deque(maxlen=silence_window_vadframes)
        while True:
            observation_window.append(await(self.is_speech_queue.get()))
            if len(observation_window) == silence_window_vadframes and\
            sum(observation_window)/len(observation_window) < SILENCE_THRESHOLD:
                return True

    async def await_stopword(self, stopword_list):
        self.check_silence = True
        self.is_speech_queue = asyncio.Queue()
        self.check_stopwords = True
        self.stopword_queue = asyncio.Queue()
        self.frames = bytearray()
        while True:
            stopword = (await self.stopword_queue.get()).lower()
            if any(sl in stopword for sl in stopword_list):
                return True

    async def await_time(self, time):
        await asyncio.sleep(time)
        return True
    
    def clear_listen_resources(self):
        self.check_silence = False
        self.check_stopwords = False
        self.stopword_queue = asyncio.Queue()
        self.is_speech_queue = asyncio.Queue()
        self.frames = bytearray()






        


 
    async def say(self, quote, hangup=False, final_pause=0, file_=False):
        begin_len = len(self.outbound_bytes)
        if not file_:
            async with tts_lock:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'{tts_url}/generate', json=quote) as resp:
                        async with aiofiles.open('temp.wav', 'wb+') as f:
                            await f.write(await resp.read())
            self.conversation_log.append(f"bot: {quote}")
        else:
            cmd = f"cp {quote} temp.wav"
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            so, se = await proc.communicate()
            print(se, flush=True)
        await self.pause(0.5)
        await self.send_outbound()
        await self.pause(final_pause)
        return len(self.outbound_bytes) 

    async def ask(self, question, await_silence=False, stopword_list=None, wait_time=None, minimum_turn_time=3, silence_window=1):
        assert (await_silence or stopword_list or wait_time), "The bot must be listening for something"
        end_speech_pos = await self.say(question)
        start_timepoint = len(self.internal_bytes)
        await self.add_timer(end_speech_pos).wait()
        print("asked", question)
        listeners = []
        if wait_time:
            listeners.append(self.await_time(wait_time))
        if stopword_list:
            listeners.append(self.await_stopword(stopword_list))
        if await_silence:
            listeners.append(self.await_silence(minimum_turn_time=minimum_turn_time, silence_window=silence_window))
        print('started listening', flush=True)
        print("now_end_pos", self.outbound_pos)
        await asyncio.wait(listeners, return_when=asyncio.FIRST_COMPLETED)
        self.clear_listen_resources()
        print('finished listening')
        send_bytes = self.internal_bytes[start_timepoint:]
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{stt_url}/process-bytes', data=send_bytes) as resp:
                callee_says = await resp.text()
                print("callee", callee_says, flush=True)
                self.conversation_log.append(f"callee: {callee_says}")
                retval = callee_says
        return retval

    async def receive_inbound(self, received_bytes):
        self.internal_bytes.extend(self.convert_to_16khz(received_bytes))
        self.internal_pos = len(self.internal_bytes)
        await self.check_timers()
        await self.listen()



    @abstractmethod
    def convert_to_16khz(self, bytes_):
        #This should convert to a PCM bytestream of 16khz signed 16 bit integer audio,
        #which is used by both tts and whisper. It should be fast enough to not appreciably block
        #It needs to be pretty quick since it is called every time a frame is received
        #from the audio device
        pass

    @property
    @abstractmethod
    def ffmpeg_convert_to_outbound(self):
        #this should return an ffmpeg command that converts a file named temp.wav (whose format is fixed0
        #to a raw stream of bytes appropriate for the output audio device.
        #The example below returns a raw mulaw stream for telephony
        #return "ffmpeg -i temp.wav -ar 8000 -f mulaw -acodec pcm_mulaw output.raw"
        pass
 

    async def send_outbound(self):
        proc = await asyncio.create_subprocess_shell(
            self.ffmpeg_convert_to_outbound,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        so, se = await proc.communicate()
        async with aiofiles.open('output.raw', 'rb') as f:
            self.outbound_bytes.extend((await f.read()))
        proc = await asyncio.create_subprocess_shell(
            "rm temp.wav output.raw",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    @property
    @abstractmethod
    def INBOUND_SAMPLE_RATE(self):
        pass

    @property
    @abstractmethod
    def INBOUND_BYTE_WIDTH(self):
        pass

    @property
    @abstractmethod
    def OUTBOUND_SAMPLE_RATE(self):
        pass

    @property
    @abstractmethod
    def OUTBOUND_BYTE_WIDTH(self):
        pass

    @property
    @abstractmethod
    def OUTBOUND_ZERO_BYTE(self):
        pass
