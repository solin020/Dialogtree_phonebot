from .database import Patient, Takes, Interaction, Alias
import requests
from bs4 import BeautifulSoup
from .prompt import extract_drug_interactions, extract_adverse_reactions
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select


URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "atsalugpiaq")

async def add_drugs(patient_id:str,phone_number:str, drugs:list[tuple[str,str]], db:AsyncSession):
    db.add(Patient(patient_id=patient_id, phone_number=phone_number))
    for (rxcui, drugname) in drugs:
        if len(list((await (db.exec(
            select(Alias).where(Alias.rxcui==rxcui and Alias.drugname==drugname)
        ))).all())) == 0:
            db.add(Alias(rxcui=rxcui,name=drugname))
    await db.commit()
    


    def dummy(tx, patient, drugs):
        tx.run("MERGE (:PATIENT {name: $patient})",patient=patient)
        for (rxcui, drugname) in drugs:
            db.add(Alias(rxcui=rxcui,name=drugname))
            get_drug_interactions(rxcui, drugname)
            tx.run("MERGE (:DRUG {rxcui: $drug})", drug=rxcui)
            tx.run("MATCH (d:DRUG), (p:PATIENT) "
                "WHERE d.rxcui = $drug AND p.name = $patient "
                "MERGE (p)-[:TAKES]->(d)", patient=patient, drug=rxcui)
            

def get_drug_interactions(rxcui, drugname):
    data = requests.get(f'https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?drug_name={rxcui}').json()['data'][0]['setid']
    for d in data:
        try:
            page = BeautifulSoup(requests.get(f'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={d['setid']}').text, 'html.parser')
            paragraph = page.find('a', text='DRUG INTERACTIONS').find_next_sibling().get_text()
            dacts = extract_drug_interactions(drugname, paragraph)
            break
        except AttributeError as e:
            continue
    else:
        return 'no drug interactions found'

    
