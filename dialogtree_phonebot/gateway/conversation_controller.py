import asyncio, aiohttp, aiofiles, collections, webrtcvad
from ..config import tts_url, stt_url
import numpy as np

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

  
OUTBOUND_BUFFER = 640
SILENCE_THRESHOLD = 0.4

class EndCall(Exception):
    pass


class ConversationController():
    def __init__(self):
        self.participant_internal_track = bytearray()#translated to 16khz pcm_s16le mono from inbound audio (8Khz mulaw for phone)
        self.outbound_internal_track = bytearray()#robot's voice in its internal 16khz pcm_s16le mono representation 
        self.participant_received_pos = 0
        self.vad_pos = 0
        self.outbound_sent_pos = 0
        self.timers = {}
        self.call_over = False
        self.end_event = asyncio.Event()



    async def check_timers(self):
        evict_flags = []
        for k, v in self.timers.items():
            if self.outbound_sent_pos > k:
                v.set()
                evict_flags.append(k)
        for k in evict_flags:
            self.timers.pop(k)


    def add_timer(self, end_pos):
        timer = asyncio.Event()
        self.timers[end_pos] = timer
        return timer


    async def receive_inbound(self, received_bytes):
        self.participant_internal_track.extend(received_bytes)
        self.participant_received_pos = len(self.participant_internal_track)
        await self.check_timers()

    def send_outbound(self):
        if self.call_over:
            raise EndCall
        buffer_pos = self.participant_received_pos + OUTBOUND_BUFFER
        silence_needed = buffer_pos - len(self.outbound_internal_track)
        if silence_needed > 0:
            self.outbound_internal_track.extend(silence_needed*b'\x00')
        retval = self.outbound_internal_track[self.outbound_sent_pos:buffer_pos]
        self.outbound_sent_pos = buffer_pos
        return retval
    

    def pause(self, seconds):
        self.outbound_internal_track.extend(seconds_to_time(seconds) * b'\x00')
        return len(self.outbound_internal_track)

    async def await_silence(self, *args, **kwargs):
        force_end = asyncio.ensure_future(asyncio.sleep(70))
        silence_window_vadframes = int(TURN_WAIT_INTERVAL//0.03)
        observation_window = collections.deque(maxlen=silence_window_vadframes)
        self.vad_pos = len(self.participant_internal_track)
        while True:
            if force_end.done():
                return True
            await asyncio.sleep(SILENCE_CHECK_INTERVAL)
            while True:
                frame = self.participant_internal_track[self.vad_pos:self.vad_pos + VAD_FRAME_BYTES]
                self.vad_pos += VAD_FRAME_BYTES
                if self.vad_pos > len(self.participant_internal_track):
                    self.vad_pos = len(self.participant_internal_track)
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
                async with session.post(f'{stt_url}/process-stopword', data=self.participant_internal_track[-STOPWORD_WINDOW:]) as resp:
                    stopword = await resp.text()
                    print('stopword', stopword, flush=True)
                    if any(sl.lower() in stopword.lower() for sl in stopword_list):
                        return stopword

    async def await_time(self, time):
        await asyncio.sleep(time)
        return True
    

    #Files to be played must be in the 16khz pcm_s16le mono wav format
    async def play_file(self, file_:str, final_pause:float=0, initial_pause:float=0.5):
        async with aiofiles.open(file_) as f:
            self.outbound_internal_track.extend((await f.read())[44:])
        await self.pause(initial_pause)
        self.send_outbound()
        await self.pause(final_pause)
        return len(self.outbound_internal_track) 


    async def say(self, quote:str, final_pause:float=0, initial_pause:float=0.5):
        async with tts_lock:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{tts_url}/generate', json=quote) as resp:
                    bytes_ = (await resp.read())[44:]
        resample = 16000 / 22050
        code = '<i2'
        #The voice seems to come in too loud so i reduce the volume this way
        y = np.frombuffer(bytes_, code) >> 1
        oldxlen = y.size
        oldx = np.linspace(0, oldxlen, oldxlen)
        newx = np.linspace(0, oldxlen, int(oldxlen*resample))
        new_bytes_ = np.interp(newx, oldx, y).astype('<i2').tobytes()
        self.pause(initial_pause)
        self.outbound_internal_track.extend(new_bytes_)
        self.pause(final_pause)
        return len(self.outbound_internal_track) 

    async def ask(
            self, 
            question, 
            file=None, 
            await_silence=True, 
            stopword_list=None, 
            wait_time=30, 
            minimum_turn_time=3, 
            silence_window=1, 
            final_pause=0.5,return_stopword=False):
        await self.say(question, final_pause=final_pause)
        if file is not None:
            await self.play_file(file)
        end_speech_pos = self.pause(2)
        print('end_speech_pos', end_speech_pos)
        await self.add_timer(end_speech_pos).wait()
        print("asked", question)
        start_timepoint = len(self.participant_internal_track) - seconds_to_time(2)
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
        send_bytes = self.participant_internal_track[start_timepoint:]
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{stt_url}/process-bytes', data=send_bytes) as resp:
                callee_says = await resp.text()
                print("callee", callee_says, flush=True)
                retval = callee_says
        return retval

    def goodbye(self):
        print('goodbye')
        self.call_over = True
        self.end_event.set()
