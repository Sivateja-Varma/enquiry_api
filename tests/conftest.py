from fastapi.testclient import TestClient
from sqlmodel import create_engine,Session,SQLModel
from app.app import app as fastapi_app,get_user
from app.app import User
import app.db
import pytest


sqlite_db_name="test.db"
sqlite_url=F"sqlite:///{sqlite_db_name}"
connect_args={"check_same_thread":False}
@pytest.fixture(name="engine")
def test_engine():
    engine=create_engine(sqlite_url,connect_args=connect_args)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
 

@pytest.fixture(name="session")
def test_session(engine):
  with Session(engine) as session:
    yield session



@pytest.fixture(name="allowed")   
def test_host():
  def get_host_test() :
     return User(id=1,name="sivateja",role="admin")
  
  fastapi_app.dependency_overrides[get_user]=get_host_test
  yield
  fastapi_app.dependency_overrides.clear()

@pytest.fixture(name="client")
def test_client(session,engine):
   app.db.engine=engine

   def get_session_test():
      return session
   
   fastapi_app.dependency_overrides[app.db.get_session]=get_session_test

   with TestClient(fastapi_app) as client:
      yield client

   fastapi_app.dependency_overrides.clear()   


     

