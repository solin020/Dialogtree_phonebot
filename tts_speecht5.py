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
import time

processor = SpeechT5Processor.from_pretrained("/data1/models/speecht5_tts")
model = SpeechT5ForTextToSpeech.from_pretrained("/data1/models/speecht5_tts").to(device='cuda')
vocoder = SpeechT5HifiGan.from_pretrained("/data1/models/speecht5_hifigan").to(device='cuda')
embeddings_dataset = load_dataset("/data1/models/cmu-arctic-xvectors", split="validation")
speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0).to(device='cuda')

app = Starlette()
@app.route('/generate', methods=['GET'])
async def generate(request):
    with torch.no_grad():
        text = await request.json()
        start_time = time.time()
        inputs = processor(text=text, return_tensors="pt").to(device='cuda')
        speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)
        tempf = BytesIO()
        sf.write(tempf, speech.cpu().numpy(), samplerate=16000, format='wav')
        print('tts_time:', time.time()-start_time)
        return PlainTextResponse(tempf.getvalue())
