import asyncio, webrtcvad, aiohttp, aiofiles, collections
from functools import cached_property
from abc import ABC, abstractmethod
import torch, numpy as np
import vap.model
from vap.utils import batch_to_device
import wave
from vap.plot_utils import plot_stereo

prosody_model = vap.model.VapGPT()
state_dict = vap.model.load_older_state_dict('VAP_3mmz3t0u_50Hz_ad20s_134-epoch9-val_2.56.ckpt')
prosody_model.load_state_dict(state_dict, strict=False)
prosody_model = prosody_model.to("cuda:0")

vad = webrtcvad.Vad()
vad.set_mode(1)
tts_lock = asyncio.Lock()

INTERNAL_SAMPLE_RATE=16000
INTERNAL_BYTE_WIDTH=2
PROSODY_INTERVAL = 0.25
PROSODY_WINDOW = 5*INTERNAL_SAMPLE_RATE*INTERNAL_BYTE_WIDTH
STOPWORD_INTERVAL = 0.75
STOPWORD_WINDOW = int(1.5*INTERNAL_SAMPLE_RATE*INTERNAL_BYTE_WIDTH)
TURN_WAIT_INTERVAL = 1*INTERNAL_SAMPLE_RATE*INTERNAL_BYTE_WIDTH


def seconds_to_time(t):
    return INTERNAL_BYTE_WIDTH * int(t*INTERNAL_SAMPLE_RATE)

  
OUTBOUND_BUFFER = 600
tts_url = "http://localhost:5001"
stt_url = "http://localhost:5002"
llm_url = "http://localhost:5003"


class ConversationController(ABC):
    def __init__(self):
        self.patient_track = bytearray()#translated to 16khz pcm from inbound audio (8Khz mulaw for phone)
        self.robot_track = bytearray()#the robot's voice in native 16Khz pcm
        self.outbound_bytes = bytearray()#robot's voice after being resampled for the appropriate output device (8Khz mulaw for phone)
        self.patient_pos = 0
        self.robot_pos = 0
        self.outbound_pos = 0
        self.conversation_log = []
        self.timers = {}
        self.turn_switch = None


    async def check_timers(self):
        evict_flags = []
        for k, v in self.timers.items():
            if self.robot_pos > k:
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
        received_pos = int(len(self.patient_track) * self.outbound_over_internal)
        buffer_pos = received_pos + OUTBOUND_BUFFER
        silence_needed = buffer_pos - len(self.outbound_bytes)
        if silence_needed > 0:
            self.outbound_bytes.extend(silence_needed*self.OUTBOUND_ZERO_BYTE)
            self.robot_track.extend(int(silence_needed/self.outbound_over_internal)*b'\0')
        retval = self.outbound_bytes[self.outbound_pos:buffer_pos]
        self.outbound_pos = buffer_pos
        self.robot_pos = len(self.robot_track)
        return retval
    

    async def pause(self, seconds):
        self.outbound_bytes.extend(int(seconds_to_time(seconds) * self.outbound_over_internal) * self.OUTBOUND_ZERO_BYTE)
        self.robot_track.extend(int(seconds_to_time(seconds) ) * b'\0')

    async def await_silence(self, *args, **kwargs):
        while True:
            await asyncio.sleep(PROSODY_INTERVAL)
            patient_track_tensor = torch.tensor((np.frombuffer(self.patient_track[-PROSODY_WINDOW:], dtype='<i2') / 32768).astype(np.float32))
            waveform = patient_track_tensor.unsqueeze(0)
            waveform = torch.cat((waveform, torch.zeros_like(waveform))).unsqueeze(0).to(device='cuda:0')
            out = batch_to_device(prosody_model.probs(waveform), "cpu")
            p_future = out["p_future"][0, -1, 0].cpu()
            print(f'{p_future=}')
            if p_future<0.75:
                if self.turn_switch is None:
                    self.turn_switch = len(self.patient_track)
                elif len(self.patient_track) - self.turn_switch > TURN_WAIT_INTERVAL:
                    self.turn_switch = None
                    return True
            else:
                self.turn_switch = None


    async def await_stopword(self, stopword_list):
        while True:
            await asyncio.sleep(STOPWORD_INTERVAL)
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{stt_url}/process-bytes', data=self.patient_track[-STOPWORD_WINDOW:]) as resp:
                    stopword = await resp.text()
                    print('stopword', stopword, flush=True)
                    if any(sl in stopword for sl in stopword_list):
                        return True

    async def await_time(self, time):
        await asyncio.sleep(time)
        return True
    






        


 
    async def say(self, quote, hangup=False, final_pause=0, file_=False, initial_pause=0.5):
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
        await self.pause(initial_pause)
        await self.send_outbound()
        await self.pause(final_pause)
        return len(self.robot_track) 

    async def ask(self, question, await_silence=False, stopword_list=None, wait_time=None, minimum_turn_time=3, silence_window=1, final_transcribe=True, final_pause=1.5):
        assert (await_silence or stopword_list or wait_time), "The bot must be listening for something"
        end_speech_pos = await self.say(question, final_pause=final_pause)
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
        start_timepoint = len(self.patient_track)
        await asyncio.wait(listeners, return_when=asyncio.FIRST_COMPLETED)
        print('finished listening')
        send_bytes = self.patient_track[start_timepoint:]
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{stt_url}/process-bytes', data=send_bytes) as resp:
                callee_says = await resp.text()
                print("callee", callee_says, flush=True)
                self.conversation_log.append(f"callee: {callee_says}")
                retval = callee_says
        return retval

    async def receive_inbound(self, received_bytes):
        self.patient_track.extend(self.convert_to_16khz(received_bytes))
        self.robot_track.extend(b'\0'*(len(self.patient_track)-len(self.robot_track)))
        self.patient_pos = len(self.patient_track)
        self.robot_pos = len(self.robot_track)
        await self.check_timers()



    @abstractmethod
    def convert_to_16khz(self, bytes_):
        #This should convert to a PCM bytestream of 16khz signed 16 bit integer audio,
        #which is used by both tts and whisper. It should be fast enough to not appreciably block
        #It needs to be pretty quick since it is called every time a frame is received
        #from the audio device
        pass

    def _ffmpeg_convert_to_outbound(self):
        with wave.open('temp.wav', 'rb') as f:
            self.robot_track.extend(f.readframes(f.getnframes()))

    @property
    @abstractmethod
    def ffmpeg_convert_to_outbound(self):
        #this should return an ffmpeg command that converts a file named temp.wav (whose format is fixed0
        #to a raw stream of bytes appropriate for the output audio device.
        #The example below returns a raw mulaw stream for telephony
        #return "ffmpeg -i temp.wav -ar 8000 -f mulaw -acodec pcm_mulaw output.raw"
        pass
 

    async def send_outbound(self):
        self._ffmpeg_convert_to_outbound()
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
