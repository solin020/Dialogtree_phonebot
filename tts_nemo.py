from starlette.responses import PlainTextResponse
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.routing import Route
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import torch
import soundfile as sf
from datasets import load_dataset
from io import BytesIO
import os
debug = os.getenv('debug')
if debug:
    import time


# Load FastPitch
from nemo.collections.tts.models import FastPitchModel
spec_generator = FastPitchModel.from_pretrained("nvidia/tts_en_fastpitch").eval()

# Load vocoder
from nemo.collections.tts.models import HifiGanModel
model = HifiGanModel.from_pretrained(model_name="nvidia/tts_hifigan")


app = Starlette()
@app.route('/generate', methods=['GET'])
async def generate(request):
    text = await request.json()
    tempf = generate(text)
    return PlainTextResponse(tempf.getvalue())


def generate(text):
    if debug:
        start_time = time.time()
    parsed = spec_generator.parse(text)
    spectrogram = spec_generator.generate_spectrogram(tokens=parsed)
    audio = model.convert_spectrogram_to_audio(spec=spectrogram)
    tempf = BytesIO()
    sf.write(tempf, audio.to('cpu').detach().numpy()[0], samplerate=22050, format='wav')
    if debug:
        print('tts_time:', time.time()-start_time)
    return tempf
