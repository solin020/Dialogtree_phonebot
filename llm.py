from starlette.responses import PlainTextResponse
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.routing import Route
from transformers import LlamaTokenizer, LlamaForCausalLM
import torch
model = LlamaForCausalLM.from_pretrained('/data1/models/vicuna-7b-v1.3', load_in_8bit=True, torch_dtype=torch.float16, device_map="auto")
tokenizer = LlamaTokenizer.from_pretrained('/data1/models/vicuna-7b-v1.3')


app = Starlette()


@app.route('/generate', methods=['POST'])
async def process_array(request):
    history = await request.json()
    print(history)
    init_str = ""
    for role, message in history:
        if role == 'USER':
            init_str += f"\nUSER: {message}"
        elif role == 'SYSTEM':
            init_str += f"\nSYSTEM: {message}"
    init_str +="\nSYSTEM:"
    init_str = init_str.strip()
    reply = tokenizer.decode(model.generate(tokenizer(init_str, return_tensors="pt").input_ids.to(device="cuda:0"), 
                                            max_new_tokens=40)[0], skip_special_tokens=True)
    reply = reply[len(init_str):]
    print(reply)
    reply = reply.split('SYSTEM:')[-1]
    reply = reply.split('USER:')[0]
    return PlainTextResponse(reply)
