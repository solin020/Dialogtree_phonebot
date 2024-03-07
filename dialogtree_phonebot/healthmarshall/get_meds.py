import json, requests, spacy, __main__
from prompt import complete, generate_prompt
from patient_database import add_drugs
import time
from apptypes import AnnotatedDocument, Span, Cui, Interaction
from load_model import nlp, linker, link_rxcui
import re
split_exp = '^[A-Z ]+:.*$'



with open('instruction.txt') as f:
    medication_instruction = f.read()

def make_chatgpt_request(instruction, input=None):
    request = generate_prompt(instruction, input)
    return complete(request)

def split_sents(a, amount=20):
     return ''.join([str(s) for s in list(nlp(a).sents)][:amount])
    
def get_sections(notes):
    current_note_sections_list = []
    current_section = []
    for line in notes.split('\n'):
        if re.match(split_exp, line):
            if current_section:
                section_string = '\n'.join(current_section)
                current_note_sections_list.append(section_string)
            current_section = [line]
        else:
            current_section.append(line)
    section_string = '\n'.join(current_section)
    current_note_sections_list.append(section_string)
    return current_note_sections_list


def get_meds(notes, patient):
    drugs = []
    test_output = []
    for ipt in get_sections(notes):
        sents = [str(s) for s in nlp(ipt).sents if str(s).strip()]
        time.sleep(0.1)
        i=0
        while True:
            if i >= len(sents):
                break
            s = ''.join(sents[i:i+20])
            s1 = ''.join(sents[i:i+10])
            s2 = sents[i+10:i+20]
            if not s2:
                s2=''
            else:
                s2 = ''.join(s2)
            meds = make_chatgpt_request(instruction=medication_instruction, input=s)
            test_output.append([s, meds, s1, s2])
            i += 10
    sec_pos = 0
    start_pos = 0
    retval = []
    first_section = True
    for full_s, meds, s1, s2 in test_output:
        print('MEDS', meds)
        if first_section:
            first_section = False
            next_pos = sec_pos + len(full_s)
            searchand = full_s
        elif not s2:
            first_section=True
            continue
        else:
            searchand = s2
            next_pos = sec_pos + len(s2)
        print('SEARCHAND', searchand)
        if 'medicine=>' in meds:
            for med_section in [s for s in meds.split('medicine=>') if s]:
                med_section = 'medicine=>' + med_section
                portions = {l.split('=>')[0]:l.split('=>')[1] for l in med_section.split('\n') if '=>' in l}
                med_name = portions['medicine']
                med_pos = searchand.find(med_name)
                if med_name == 'nm' or med_pos == -1:
                    continue
                candidates = linker.candidate_generator([med_name], k=1)
                if not candidates:
                    continue
                if not candidates[0]:
                    continue
                concept = linker.kb.cui_to_entity[candidates[0][0].concept_id]
                if concept.definition and (rxcui:=link_rxcui(concept.concept_id, med_name)):
                    drugs.append((rxcui, med_name))
                    retval.append(Span(
                        tag='SPAN',
                        content=notes[start_pos:sec_pos+med_pos]
                    ))
                    retval.append(Cui(
                        tag='CUI',
                        found_text=med_name,
                        concept_id=f'cui: {concept.concept_id}, rxcui:{rxcui}',
                        definition=concept.definition,
                        canonical_name=concept.canonical_name,
                        aliases=concept.aliases,
                        interactions=[],
                        dose=portions.get('dose', 'nm'),
                        duration=portions.get('duration', 'nm'),
                        form=portions.get('form', 'nm'),
                        frequency=portions.get('frequency', 'nm'),
                        reason=portions.get('reason', 'nm'),
                    ))
                start_pos = sec_pos + med_pos + len(med_name)
        sec_pos = next_pos

    retval.append(Span(
        tag='SPAN',
        content=notes[start_pos:]
    ))
    add_drugs(patient, drugs)
    return AnnotatedDocument(entities=retval)