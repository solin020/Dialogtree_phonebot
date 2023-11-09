from starlette.responses import PlainTextResponse
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.routing import Route
import torch
from io import BytesIO
import time
from TTS.utils.synthesizer import Synthesizer
from config import model_directory
import os

model_path = os.path.join(model_directory, 'tts_model', 'model_file.pth')
config_path = os.path.join(model_directory, 'tts_model', 'config.json')
vocoder_path = os.path.join(model_directory, 'tts_vocoder', 'model_file.pth')
vocoder_config_path = os.path.join(model_directory, 'tts_vocoder', 'config.json')
speakers_file_path=None
synthesizer = Synthesizer(
    tts_checkpoint=model_path,
    tts_config_path=config_path,
    vocoder_checkpoint=vocoder_path,
    vocoder_config=vocoder_config_path,
    encoder_checkpoint="",
    encoder_config="",
    use_cuda=True,
)

app = Starlette()
@app.route('/generate', methods=['GET'])
async def generate(request):
    text = await request.json()
    start_time = time.time()
    speaker_idx = ""
    language_idx = ""
    style_wav = None
    wavs = synthesizer.tts(text, speaker_name=speaker_idx, language_name=language_idx, style_wav=style_wav)
    tempf = BytesIO()
    synthesizer.save_wav(wavs, tempf)
    print('tts_time:', time.time()-start_time)
    return PlainTextResponse(tempf.getvalue())
