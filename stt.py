from starlette.responses import PlainTextResponse
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.routing import Route
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import numpy as np

processor = WhisperProcessor.from_pretrained("/data1/models/whisper-large-v2")
model = WhisperForConditionalGeneration.from_pretrained("/data1/models/whisper-large-v2").to(device='cuda')
model.config.forced_decoder_ids = None
app = Starlette()


@app.route('/process-bytes', methods=['POST'])
async def process_array(request):
    audio = (np.frombuffer(await request.body(), dtype='<i2') / 32768).astype(np.float32)
    input_features = processor(audio, sampling_rate=16000, return_tensors="pt").input_features.to(device='cuda')
    predicted_ids = model.generate(input_features)[0]
    transcription = processor.decode(predicted_ids, skip_special_tokens=True)
    return PlainTextResponse(transcription)




