from starlette.responses import PlainTextResponse
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.routing import Route
import torch
from io import BytesIO
import time
from TTS.utils.synthesizer import Synthesizer

model_path='/home/solin020/.local/share/tts/tts_models--en--ljspeech--tacotron2-DDC_ph/model_file.pth'
config_path='/home/solin020/.local/share/tts/tts_models--en--ljspeech--tacotron2-DDC_ph/config.json'
speakers_file_path=None
vocoder_path='/home/solin020/.local/share/tts/vocoder_models--en--ljspeech--univnet/model_file.pth'
vocoder_config_path='/home/solin020/.local/share/tts/vocoder_models--en--ljspeech--univnet/config.json'
synthesizer = Synthesizer(
    tts_checkpoint=model_path,
    tts_config_path=config_path,
    tts_speakers_file=speakers_file_path,
    tts_languages_file=None,
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
