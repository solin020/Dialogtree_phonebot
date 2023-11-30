from starlette.responses import PlainTextResponse, JSONResponse
from starlette.requests import Request
from starlette.applications import Starlette
from starlette.routing import Route
from transformers import LlamaTokenizer, LlamaForCausalLM
import torch
import os
debug = os.getenv('debug')
import time, re, regex
import exllama_interact

llama_model = LlamaForCausalLM.from_pretrained('./models/llama-7b-hf')
llama_tokenizer = LlamaTokenizer.from_pretrained('./models/llama-7b-hf')

app = Starlette()


@app.route('/generate', methods=['POST'])
async def process_array(request):
    history = await request.json()
    start_time = time.time()
    speaker, utterance = history[-1]
    if speaker == 'USER':
        response = await exllama_interact.converse(utterance)
        response = re.sub(' {2,}', ' ', re.sub('\*.+\*', '', response))
        print('llm_time', time.time() - start_time)
        return PlainTextResponse(response)


@app.route('/perplexity', methods=['POST'])
async def perplexity(request):
    conversation = await request.json()
    tokenizer_conversation = []
    for speaker, sentence in conversation:
        if speaker == 'USER':
            tokenizer_conversation.append(('USER', llama_tokenizer.convert_tokens_to_ids(llama_tokenizer.tokenize(sentence))))
        elif speaker == 'SYSTEM':
            tokenizer_conversation.append(('SYSTEM', llama_tokenizer.convert_tokens_to_ids(llama_tokenizer.tokenize(sentence))))
    tokens_tensor = []
    for speaker, sentence in tokenizer_conversation:
        tokens_tensor +=  sentence
    tokens_tensor = torch.tensor([tokens_tensor])
    with torch.no_grad():
        retval = 0
        ixs = llama_tokenizer.encode(sentence)
        probs = torch.nn.Softmax(dim=-1)(llama_model(tokens_tensor).logits[0])
        i = 0
        toknum = 0
        retval = 0
        for speaker, token_ids in tokenizer_conversation:
            for ix in token_ids:
                if speaker == 'USER':
                    retval += -torch.log(probs[i][ix])
                    toknum += 1
                i += 1
        return JSONResponse(float(retval.cpu().numpy())/toknum)
