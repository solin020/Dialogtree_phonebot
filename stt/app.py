from starlette.responses import PlainTextResponse
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.routing import Route
from transformers import WhisperProcessor, WhisperForConditionalGeneration, WhisperTokenizer
import numpy as np
import os
import wave
import time
from ..config import model_directory
stt_model_dir = os.path.join(model_directory, 'whisper-large-v2')

processor = WhisperProcessor.from_pretrained(stt_model_dir)
model = WhisperForConditionalGeneration.from_pretrained(stt_model_dir).to(device='cuda:1').eval()
tokenizer = WhisperTokenizer.from_pretrained(stt_model_dir)
stopword_prompt_ids = tokenizer.get_prompt_ids("Say yes, no, or continue to move on. Are you ready?", return_tensors="pt").to(device='cuda:1')

model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(language="english", task="transcribe")
app = Starlette()


@app.route('/process-bytes', methods=['POST'])
async def process_array(request):
    start_time = time.time()
    audio = (np.frombuffer(await request.body(), dtype='<i2') / 32768).astype(np.float32)
    transcription = transcribe(audio) 
    print('stt time', time.time()-start_time)
    return PlainTextResponse(transcription)

@app.route('/process-stopword', methods=['POST'])
async def process_array(request):
    start_time = time.time()
    audio = (np.frombuffer(await request.body(), dtype='<i2') / 32768).astype(np.float32)
    transcription = transcribe(audio) 
    print('stopword time', time.time()-start_time)
    return PlainTextResponse(transcription)

def transcribe(audio, prompt=None):
    input_features = processor(audio, sampling_rate=16000, return_tensors="pt").input_features.to(device='cuda:1')
    predicted_ids = model.generate(input_features, prompt_ids=prompt)[0]
    transcription = processor.decode(predicted_ids, skip_special_tokens=True)
    return transcription

with wave.open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'warmup.wav')) as f:
    start_time = time.time()
    frames = f.readframes(f.getnframes())
    audio = (np.frombuffer(frames, dtype='<i2') / 32768).astype(np.float32)
    transcribe(audio)

    
