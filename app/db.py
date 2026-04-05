from typing import Annotated,Literal,List,Optional
from datetime import UTC,datetime,timezone
from uuid import UUID
from enum import Enum
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select,Relationship

class UserRole(str, Enum):
    admin = "admin"
    user = "user"

class User(SQLModel,table=True):
    id : int|None = Field(default=None,primary_key=True)
    name : Annotated[str,Field(max_length=100,min_length=3,unique=True)]
    role : UserRole = Field(default=UserRole.user)
    hash_pass:str 
    cars: List["Car"] = Relationship(back_populates="owner")


class Car(SQLModel,table=True):
  id : int | None = Field(primary_key=True,default=None)
  name : Annotated[str,Field(min_length=3,max_length=40)]
  hp  : int | None = Field(default=None)
  model : str = Field(default=None)
  enquiry_date :Annotated[datetime,Field(default_factory=lambda:datetime.now(timezone.utc))]
  owner_id: int = Field(foreign_key="user.id")
  owner: Optional[User] = Relationship(back_populates="cars")

class CarPost(SQLModel):
    name : Annotated[str,Field(primary_key=True,min_length=3,max_length=40)]  
    hp  : int | None = Field(default=None)
    model : str = Field(default=None)



class UserPost(SQLModel):
    name : Annotated[str,Field(max_length=100,min_length=3)]
    hash_pass:str 
        

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///data/{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]    