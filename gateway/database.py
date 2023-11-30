from dataclasses import dataclass
from datetime import datetime
from starlette.config import Config
from sqlalchemy.types import JSON
from sqlalchemy.schema import Column
from typing import Dict, Optional, List, Any
from typing_extensions import TypedDict
from sqlmodel import Field, SQLModel, create_engine
from sqlalchemy.engine import URL
from ..config import db_username, db_password, db_host, db_name
config = Config(".env")
from sqlalchemy.engine import URL
url_object = URL.create(
    "postgresql",
    username=db_username,
    password=db_password,  # plain (unescaped) text
    host=db_host,
    database=db_name,
)

engine = create_engine(url_object)



@dataclass
class Job(SQLModel, table=True):
    job_id: str = Field(primary_key=True)
    phone_number: str
    rejects: int
    timestamp: datetime


@dataclass
class CallLog(SQLModel, table=True):
    call_sid: str = Field(primary_key=True)
    phone_number: str
    timestamp: datetime
    participant_study_id: str = Field(default="unknown")
    rejected: Optional[str] = Field(default="false")
    previous_rejects: int
    history: list[tuple[str,str]] = Field(sa_column=Column(JSON))
    syntax_grade: Optional[list] = Field(sa_column=Column(JSON), default=[])
    perplexity_grade: Optional[float] = Field(default=None)
    memory_exercise_words: Optional[List[str]] = Field(sa_column=Column(JSON), default=None)
    memory_exercise_reply: Optional[str] = Field(default=None)
    memory_grade: dict = Field(sa_column=Column(JSON), default={})
    memory_exercise_reply_2: Optional[str] = Field(default=None)
    memory_grade_2: dict = Field(sa_column=Column(JSON), default={})
    l_reply: Optional[str] = Field(default=None)
    l_grade: dict = Field(sa_column=Column(JSON), default={})
    animal_reply: Optional[str] = Field(default=None)
    animal_grade: dict = Field(sa_column=Column(JSON), default={})
    dysarthria_grade: Optional[float] = Field(default=None)
    miscellaneous: dict = Field(sa_column=Column(JSON), default={})


@dataclass
class Participant(SQLModel, table=True):
    participant_study_id: str = Field(primary_key=True)
    phone_number: str
    end_date: datetime
    start_date: datetime
    morning_time: int
    afternoon_time: int
    evening_time: int
    morning_minute: int
    afternoon_minute: int
    evening_minute: int


@dataclass
class ScheduledCall(SQLModel, table=True):
    id: str = Field( primary_key=True)
    phone_number: str
    time: datetime
    rejects: int

#by calling python database.py this is executed and the database is initialized
if __name__ == '__main__':
    SQLModel.metadata.create_all(engine)
