import asyncio, aiohttp, aiofiles, collections, webrtcvad
from functools import cached_property
from abc import ABC, abstractmethod
import numpy as np
import wave
import os
import uuid

vad = webrtcvad.Vad()
vad.set_mode(1)

tts_lock = asyncio.Lock()

INTERNAL_SAMPLE_RATE=16000
INTERNAL_BYTE_WIDTH=2
SILENCE_CHECK_INTERVAL = 0.5
STOPWORD_INTERVAL = 0.75
STOPWORD_WINDOW = int(1.5*INTERNAL_SAMPLE_RATE*INTERNAL_BYTE_WIDTH)
TURN_WAIT_INTERVAL = 3
VAD_FRAME_BYTES = INTERNAL_BYTE_WIDTH * int((INTERNAL_SAMPLE_RATE/100)*3)

def seconds_to_time(t):
    return INTERNAL_BYTE_WIDTH * int(t*INTERNAL_SAMPLE_RATE)

  
OUTBOUND_BUFFER = 600
SILENCE_THRESHOLD = 0.4
tts_url = "http://localhost:5001"
stt_url = "http://localhost:5002"
llm_url = "http://localhost:5003"


class ConversationController(ABC):
    def __init__(self):
        self.participant_track = bytearray()#translated to 16khz pcm from inbound audio (8Khz mulaw for phone)
        self.outbound_bytes = bytearray()#robot's voice after being resampled for the appropriate output device (8Khz mulaw for phone)
        self.participant_pos = 0
        self.vad_pos = 0
        self.outbound_pos = 0
        self.conversation_log = []
        self.timers = {}
        self.turn_switch = None
        self.temp_file = f'{uuid.uuid4()}.wav'
        self.output_file = f'{uuid.uuid4()}.wav'



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
        received_pos = int(len(self.participant_track) * self.outbound_over_internal)
        buffer_pos = received_pos + OUTBOUND_BUFFER
        silence_needed = buffer_pos - len(self.outbound_bytes)
        if silence_needed > 0:
            self.outbound_bytes.extend(silence_needed*self.OUTBOUND_ZERO_BYTE)
        retval = self.outbound_bytes[self.outbound_pos:buffer_pos]
        self.outbound_pos = buffer_pos
        return retval
    

    async def pause(self, seconds):
        self.outbound_bytes.extend(int(seconds_to_time(seconds) * self.outbound_over_internal) * self.OUTBOUND_ZERO_BYTE)

    async def await_silence(self, *args, **kwargs):
        force_end = asyncio.ensure_future(asyncio.sleep(70))
        silence_window_vadframes = int(TURN_WAIT_INTERVAL//0.03)
        observation_window = collections.deque(maxlen=silence_window_vadframes)
        self.vad_pos = len(self.participant_track)
        while True:
            if force_end.done():
                return True
            await asyncio.sleep(SILENCE_CHECK_INTERVAL)
            while True:
                frame = self.participant_track[self.vad_pos:self.vad_pos + VAD_FRAME_BYTES]
                self.vad_pos += VAD_FRAME_BYTES
                if self.vad_pos > len(self.participant_track):
                    self.vad_pos = len(self.participant_track)
                if len(frame) == VAD_FRAME_BYTES:
                    observation_window.append(vad.is_speech(frame, INTERNAL_SAMPLE_RATE))
                else:
                    prob = sum(observation_window) / len(observation_window)
                    print('silence prob', prob)
                    if len(observation_window) == silence_window_vadframes  and\
                    prob < SILENCE_THRESHOLD:
                        return True
                    else:
                        break


    async def await_stopword(self, stopword_list):
        force_end = asyncio.ensure_future(asyncio.sleep(70))
        while True:
            if force_end.done():
                return ""
            await asyncio.sleep(STOPWORD_INTERVAL)
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{stt_url}/process-bytes', data=self.participant_track[-STOPWORD_WINDOW:]) as resp:
                    stopword = await resp.text()
                    print('stopword', stopword, flush=True)
                    if any(sl.lower() in stopword.lower() for sl in stopword_list):
                        return stopword

    async def await_time(self, time):
        await asyncio.sleep(time)
        return True
    






        


 
    async def play_file(self, file_:str, final_pause:float=0, initial_pause:float=0.5):
        cmd = f"cp {file_} {self.temp_file}"
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        so, se = await proc.communicate()
        print(se, flush=True)
        await self.pause(initial_pause)
        await self.send_outbound()
        await self.pause(final_pause)
        return len(self.outbound_bytes) 


    async def say(self, quote:str, final_pause:float=0, initial_pause:float=0.5):
        async with tts_lock:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{tts_url}/generate', json=quote) as resp:
                    async with aiofiles.open(f'{self.temp_file}', 'wb+') as f:
                        resp_bytes = await resp.read()
                        await f.write(resp_bytes)
        await self.pause(initial_pause)
        await self.send_outbound()
        await self.pause(final_pause)
        return len(self.outbound_bytes) 

    async def ask(self, question, await_silence=False, stopword_list=None, wait_time=None, minimum_turn_time=3, silence_window=1, final_transcribe=True, final_pause=0.5,
                  return_stopword=False):
        assert (await_silence or stopword_list or wait_time), "The bot must be listening for something"
        end_speech_pos = await self.say(question, final_pause=final_pause)
        await self.add_timer(end_speech_pos).wait()
        print("asked", question)
        start_timepoint = len(self.participant_track)
        listeners = []
        if wait_time:
            listeners.append(self.await_time(wait_time))
        if stopword_list:
            listeners.append(self.await_stopword(stopword_list))
        if await_silence:
            listeners.append(self.await_silence(minimum_turn_time=minimum_turn_time, silence_window=silence_window))
        done, pending = await asyncio.wait(listeners, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
        print('finished listening')
        if return_stopword:
            return done.pop().result()
        send_bytes = self.participant_track[start_timepoint:]
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{stt_url}/process-bytes', data=send_bytes) as resp:
                callee_says = await resp.text()
                print("callee", callee_says, flush=True)
                self.conversation_log.append(f"callee: {callee_says}")
                retval = callee_says
        return retval

    async def receive_inbound(self, received_bytes):
        self.participant_track.extend(self.convert_to_16khz(received_bytes))
        self.participant_pos = len(self.participant_track)
        await self.check_timers()



    @abstractmethod
    def convert_to_16khz(self, bytes_) -> bytes:
        #This should convert to a PCM bytestream of 16khz signed 16 bit integer audio,
        #which is used by both tts and whisper. It should be fast enough to not appreciably block
        #It needs to be pretty quick since it is called every time a frame is received
        #from the audio device
        pass


    @property
    @abstractmethod
    def ffmpeg_convert_to_outbound(self) -> str:
        #this should return an ffmpeg command that converts a file named {self.temp_file} (whose format is fixed)
        #to a raw stream of bytes appropriate for the output audio device.
        #The example below returns a raw mulaw stream for telephony
        #return "ffmpeg -i {self.temp_file} -ar 8000 -f mulaw -acodec pcm_mulaw {self.output_file}"
        pass
 

    async def send_outbound(self):
        proc = await asyncio.create_subprocess_shell(
            self.ffmpeg_convert_to_outbound,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        so, se = await proc.communicate()
        async with aiofiles.open(f'{self.output_file}', 'rb') as f:
            self.outbound_bytes.extend((await f.read()))
        proc = await asyncio.create_subprocess_shell(
            f"rm {self.temp_file} {self.output_file}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    @property
    @abstractmethod
    def INBOUND_SAMPLE_RATE(self) -> int:
        pass

    @property
    @abstractmethod
    def INBOUND_BYTE_WIDTH(self) -> int:
        pass

    @property
    @abstractmethod
    def OUTBOUND_SAMPLE_RATE(self) -> int:
        pass

    @property
    @abstractmethod
    def OUTBOUND_BYTE_WIDTH(self) -> int:
        pass

    @property
    @abstractmethod
    def OUTBOUND_ZERO_BYTE(self) -> bytes:
        pass
