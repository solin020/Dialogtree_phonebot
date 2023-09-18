
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan

processor = SpeechT5Processor.from_pretrained("/data1/models/speecht5_tts")
model = SpeechT5ForTextToSpeech.from_pretrained("/data1/models/speecht5_tts")
vocoder = SpeechT5HifiGan.from_pretrained("/data1/models/speecht5_hifigan")

processor = torch.compile(processor)
model = torch.compile(model)
vocoder = torch.compile(vocoder)
