from typing import List, Union, Literal
from typing_extensions import Annotated
from pydantic import BaseModel, Field


class Interaction(BaseModel):
    interactee: str

class Cui(BaseModel):
    tag: Literal['CUI']
    found_text: str
    concept_id: str
    definition: str
    canonical_name: str
    aliases: List[str]
    interactions: List[Interaction]
    dose: str
    duration: str
    form:str
    frequency:str
    reason:str


class Span(BaseModel):
    tag: Literal['SPAN']
    content: str

EntityList = Annotated[
    Union[Cui, Span],
    Field(discriminator="tag")
]

class AnnotatedDocument(BaseModel):
    entities: List[EntityList]