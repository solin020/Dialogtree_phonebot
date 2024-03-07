import requests
import urllib.parse
import os
from starlette.config import Config
import openai
config = Config(".env")
openai.organization = "org-bblNXkHnhUHO1tRKAYvl3CpV"
openai.api_key = config("OPENAI_API_KEY")




def complete(prompt):
    completion = openai.Completion.create(
        engine="text-davinci-003", 
        prompt=prompt,
        n=1,
        stop=None,
        temperature=0.1
    )
    return completion.choices[0].text.strip()

def extract_adverse_reactions(input_text):
    """
    extract adverse reactions from dailymed cotent using text-davici-002

    :param input_text: the content of adverse reaction section in a dailymed article
    :type input_text: _str
    :return: extracted adverse reactions, separated with comma
    :rtype: str
    """
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt = f"List all adverse reactions, in the format [interaction,interaction,interaction] from the input text:\n\{input_text}",
        n=1,
        stop=None,
        temperature=0.1
    )
    adverse_reactions = response.choices[0].text.strip()
    return adverse_reactions


def extract_drug_interactions(drug_name, input_text):
    """
    extract drug interactions

    :param drug_name: the brand name or generic name of the drug
    :type drug_name: str
    :param input_text: the drug interaction section
    :type input_text: str
    :return: drug interaction pairs
    :rtype: str
    """
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt = f"List all drug interaction pairs using the format [{drug_name}|drug|interactions] from the input:\n\{input_text}",
        n=1,
        stop=None,
        temperature=0.1
    )
    drug_interactions = response.choices[0].text.strip()
    return drug_interactions




def generate_prompt(instruction, input=None):
    if input:
        return f"""{instruction} 
        Here is your input:
        {input}"""