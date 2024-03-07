import spacy
import scispacy
import sys
import json
from scispacy.linking import EntityLinker

nlp = spacy.load("en_core_sci_lg")

nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "linker_name": "rxnorm"})
linker = nlp.get_pipe('scispacy_linker')

with open('cui_to_rxcui.json') as f:
    cui_to_rxcui = json.load(f)

def link_rxcui(cui, foundstr):
    if cui not in cui_to_rxcui:
        return None
    entry = cui_to_rxcui[cui]
    if len(entry)==1:
        return list(entry.values())[0]
    else:
        base = nlp(foundstr)
        first_str = list(entry)[0]
        comparand = nlp(first_str)
        sim = base.similarity(comparand)
        for next_str in list(entry)[1:]:
            next_comparand = nlp(next_str)
            next_sim = base.similarity(next_comparand)
            if next_sim > sim:
                sim = next_sim
                first_str = next_str
        return entry[first_str]



