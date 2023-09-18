import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Text, Float, DateTime, Integer
from dataclasses import dataclass
from datetime import datetime
from starlette.config import Config
from sqlalchemy.dialects.postgresql import JSONB
from typing import Dict, Optional, List
from typing_extensions import TypedDict

config = Config(".build_env")

engine = create_engine('postgresql://postgres:password@localhost/postgres')
Session = sessionmaker(bind=engine)

Base = declarative_base()


class CallData(TypedDict, total=False):
    number: Optional[str]
    mturk_id: Optional[int]
    conversation_log: Optional[str]
    memory_exercise_words: Optional[List[str]]
    memory_exercise_reply: Optional[str]
    memory_grade: Optional[float]
    memory_exercise_reply_2: Optional[str]
    memory_grade_2: Optional[float]
    f_reply: Optional[str]
    f_grade: Optional[float]
    animal_reply: Optional[str]
    animal_grade: Optional[float]

class Patient(TypedDict, total=False):
    number: Optional[str]
    patient_id: Optional[str]

@dataclass
class CallLog(Base):
    __tablename__ = "call_logs"
     
    call_sid = Column(String, primary_key=True)

    number:str
    number = Column(String)

    patient_id:str
    patient_id = Column(String)

    data:CallData
    data = Column(JSONB)

    timestamp:datetime
    timestamp = Column(DateTime)

@dataclass
class Patient(Base):
    number:str
    number = Column(String)

    patient_id:str
    patient_id = Column(String)


def init_database():
    Base.metadata.create_all(engine)
