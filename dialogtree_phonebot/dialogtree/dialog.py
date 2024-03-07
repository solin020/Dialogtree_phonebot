
from xml.etree import ElementTree as ET
from openai import OpenAI
import textwrap
import argparse
import sys



class Branch:
    def __init__(self, node, parent):
        self.node = node
        self.parent = parent
        self.prompt, self.errorprompt, self.answerparse, *self.jumps = node
        self.jump_table = {}
        self.anonymous_jumps = []
        for j in self.jumps:
            if j.attrib.get('answer', None):
                for a in j.attrib['answer'].split(' '):
                    self.jump_table[a] = j
            elif j.attrib.get('accept', None):
                self.anonymous_jumps.append(j)

    
    async def execute(self):
        backprompt = self.parent.substitute(self.prompt)
        response = await self.parent.conversation.ask(backprompt) 
        answerparse_prompt = self.parent.substitute(
            self.answerparse, response=response, backprompt=backprompt
        )
        choice = await self.parent.complete(answerparse_prompt)
        while (pair:= await findmatch(choice, self.jump_table, self.anonymous_jumps, self.parent.functions, self.parent.context)) is None:
            error_prompt = self.parent.substitute(self.errorprompt, response=response, backprompt=backprompt)
            error_completion = await self.parent.complete(error_prompt)
            response = await self.parent.conversation.ask(error_completion)
            answerparse_prompt = self.parent.substitute(
                self.answerparse, response=response, backprompt=backprompt
            )
            choice = await self.parent.complete(answerparse_prompt)
        await self.parent.jump(pair[0], pair[1])



        


class State:
    def __init__(self, node, parent):
        self.node = node
        self.parent = parent
    
    async def execute(self):
        await self.parent.conversation.say(self.parent.substitute(self.node, self.parent.context))
        if 'nextdestination' in self.node.attrib:
            await self.parent.jump_destinations[self.node.attrib['nextdestination']].execute()
        else:
            await self.parent.jump_destinations['end'].execute()

class LLMQuestionDirect:
    def __init__(self, node, parent):
        self.node = node
        self.parent = parent
    
    async def execute(self):
        llm_input = self.parent.substitute(self.node, self.parent.context)
        await self.parent.conversation.say(await self.parent.complete(llm_input))
        if 'nextdestination' in self.node.attrib:
            await self.parent.jump_destinations[self.node.attrib['nextdestination']].execute()
        else:
            await self.parent.jump_destinations['end'].execute()

class LLMQuestionIndirect:
    def __init__(self, node, parent):
        self.node = node
        self.parent = parent
        self.userquestion, self.answerparse = node
    
    async def execute(self):
        backprompt = self.parent.substitute(self.userquestion)
        response = await self.parent.conversation.ask(backprompt)
        answerparse_prompt = self.parent.substitute(
            self.answerparse, response=response, backprompt=backprompt
        )
        await self.parent.conversation.say(await self.parent.complete(answerparse_prompt))
        if 'nextdestination' in self.node.attrib:
            await self.parent.jump_destinations[self.node.attrib['nextdestination']].execute()
        else:
            await self.parent.jump_destinations['end'].execute()

class Goodbye:
    def __init__(self, node, parent):
        self.node = node
        self.parent = parent
    
    async def execute(self):
        await self.parent.conversation.ask(self.parent.substitute(self.node, self.parent.context), wait_time=0.5)
        self.parent.conversation.goodbye()


        
async def findmatch(choice, jump_table, anonymous_jumps, functions, context):
    for key, jump in jump_table.items():
        if key.lower() in choice.lower():
            return jump, key
    for jump in anonymous_jumps:
        if (answer:= await functions[jump.attrib['accept']](choice, context)) is not None:
            return jump, answer
        
        

from typing import Callable


class Dialog:
    def __init__(self,conversation:str, treefile:str, functions:dict[str, Callable], openai_key:str, org_id:str, model:str="gpt-3.5-turbo", context={}):
        self.parse(ET.parse(treefile).getroot())
        self.functions=functions
        self.client = OpenAI(api_key=openai_key, organization=org_id)
        self.model = model
        self.conversation=conversation
        self.context = context
    
    def __init_subclass__(self, treefile:str, functions:dict[str, Callable], *args, **kwargs):
        self.parse(ET.parse(treefile).getroot())
        self.functions=functions

    
    def parse(self, root):
        self.root = root
        self.targets = [self.parse_target(tn) for tn in root]
        self.start_target = self.targets[0]
        self.jump_destinations = {}
        for t in self.targets:
            if 'destinationname' in t.node.attrib:
                self.jump_destinations[t.node.attrib['destinationname']] = t
    
    async def jump(self, node, answer=""):
        possible_destination = await self.execute_jump_function(node, answer)
        if 'nextdestination' in node.attrib:
            possible_destination = node.attrib['nextdestination']
        print('destination', possible_destination)
        if possible_destination not in self.jump_destinations:
            print(f'Invalid destination: {possible_destination}, restarting')
            await self.start()
        else:
            await self.jump_destinations[possible_destination].execute()
    
    async def execute_jump_function(self, node, answer):
        if 'function_name' in node.attrib:
            return await self.functions[node.attrib['function_name']](answer, self.context)
        elif (node.text is not None) and node.text.strip():
            ldict = {}
            exec("async def jfun(answer, context):\n" +
                        textwrap.indent(textwrap.dedent(node.text).strip(), prefix='    '), globals(), ldict)
            return await (ldict['jfun'](answer, self.context))


    
    def parse_target(self, target_node):
        match target_node.tag:
            case 'state': return State(target_node, self)
            case 'branch': return Branch(target_node, self)
            case 'llmquestion-indirect': return LLMQuestionIndirect(target_node, self)
            case 'llmquestion-direct': return LLMQuestionDirect(target_node, self)
            case 'goodbye': return Goodbye(target_node, self)

    def substitute(self, node, response=None, backprompt=None):
        start = node.text
        for item in node:
            if item.tag == 'response':
                start += response
            elif item.tag == 'backprompt':
                start += backprompt
            elif item.tag == 'context':
                start += self.context[item.attrib['key']]
            start += item.tail
        return '\n'.join(s.strip() for s in start.split('\n') if s.strip)
        
    async def start(self):
        print('started')
        await self.start_target.execute()
    
    async def complete(self, prompt):
        #print('asked bot', prompt) #disable when not debugging
        chat_completion = self.client.chat.completions.create(
        messages=[
                 {
                     "role": "user",
                     "content": "Don't be verbose. " + prompt,
                 }
             ],
             model=self.model,
        )
        return chat_completion.choices[0].message.content
