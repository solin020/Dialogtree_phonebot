from dataclasses import dataclass
from sqlmodel import Field, SQLModel
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from ..config import db_username, db_password, db_host, db_name

url = f'''postgresql+asyncpg://{db_username}:{db_password}@{db_host}/{db_name}'''

async_engine =  create_async_engine(url)
async def get_db() -> AsyncSession: # type: ignore
    async_session = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session



class Patient(SQLModel, table=True):
    patient_id: str = Field(primary_key=True)
    phone_number: str

class Takes(SQLModel, table=True):
    idno: int = Field(primary_key=True)
    patient_id: str
    rxcui: str

class Interaction(SQLModel, table=True):
    idno: int = Field(primary_key=True)
    rxcui: str
    interaction: str

class Rxcui2cui(SQLModel, table=True):
    idno: int = Field(primary_key=True)
    rxcui: str
    cui: str

class Alias(SQLModel, table=True):
    idno: int = Field(primary_key=True)
    rxcui: str
    name: str
