
import spacy, nltk
from nltk.corpus import words
from tqdm import tqdm
import json
from ..config import nlp_resources_directory
import os
valid_words = words.words()
nlp = spacy.load('en_core_web_sm')




def grade_l_test(transcript):
    l_list = []
    non_l_list = []
    for token in nlp(transcript):
        if token.is_alpha:
            lemma = token.lemma_.lower()
            if lemma.startswith('l') and lemma in valid_words:
                l_list.append(lemma)
            else:
                non_l_list.append(lemma)
    l_count = len(set(l_list))
    non_l_count = len(non_l_list)
    repeat_count = len(l_list) - l_count
    return {
        "l_count": l_count,
        "non_l_count": non_l_count,
        "repeat_count": repeat_count,
    }

with open(os.path.join(nlp_resources_directory, 'animal_prefixes.json')) as f:
    animal_prefixes = json.load(f)
animal_prefixes.sort(key=lambda x: len(x), reverse=True)

def grade_animal_test(transcript):
    base = ''
    for token in nlp(transcript):
        if token.is_alpha:
            token = nlp(token.lemma_)[0]
            base += ' ' +  token.lemma_.lower()
    base = base.strip()
    animals = set()
    non_animals = list()
    repeat_animals = list()
    while len(base) > 0:
        for p in tqdm(animal_prefixes):
            if base.startswith(p):
                if p not in animals:
                    animals.add(p)
                else:
                    repeat_animals.append(p)
                base = base[len(p):].strip()
                break
        else:
            words = base.split()
            non_animals.append(words[0])
            base = ' '.join(words[1:])
    return {'animals': list(animals), 
            'non_animals':non_animals,
            'repeat_animals': repeat_animals}

def grade_memory_test(transcript, word_list):
    word_list = set(str(nlp(w)[0].lemma_) for w in word_list)
    remember_count = 0
    irrelevant_count = 0
    print(word_list)
    for token in nlp(transcript):
        if token.is_alpha:
            tokenstr = nlp(str(token.lemma_).lower())[0].lemma_
            print(tokenstr)
            if tokenstr in word_list:
                word_list.remove(tokenstr)
                remember_count += 1
            else:
                irrelevant_count += 1
    return {'remember_count': remember_count,
            'irrelevant_count': irrelevant_count}
