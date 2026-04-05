from fastapi import FastAPI,Response,status,HTTPException,Depends
from contextlib import asynccontextmanager
from sqlmodel import select
from fastapi.security import HTTPBearer
from .db import SessionDep,create_db_and_tables,Car,CarPost,User,UserPost
from typing import TypeVar,Generic
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt,JWTError
from datetime import UTC,datetime,timedelta,timezone
import logging


logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
Formatter=logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')

file_handler=logging.FileHandler("error.log")
file_handler.setFormatter(Formatter)
logger.addHandler(file_handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield




app = FastAPI(version="app/v1",lifespan=lifespan)
T=TypeVar("T")

class Response(BaseModel,Generic[T]):
   data:T

hashing = CryptContext(schemes=["bcrypt"],deprecated="auto")
SECRET_KEY="secret"
ALGORITHM="HS256"

def hashed_password(password:str):
   return hashing.hash(password)
def unhash_password(password:str,hashed):
   return hashing.verify(password,hashed)
def create_access_token(data:dict):
   token=data.copy()
   expire=datetime.now(timezone.utc)+timedelta(minutes=30)
   token.update({"exp":expire})
   return jwt.encode(token,SECRET_KEY,algorithm=ALGORITHM)
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None





@app.post("/user",status_code=201)
async def RegisterUser(data:UserPost,session:SessionDep):
      try:
         user=User(
            name=data.name,
            hash_pass=hashed_password(data.hash_pass),
            role="admin"
         )
         session.add(user)
         session.commit()
         session.refresh(user)
      except Exception as e:
         logger.exception("error while registring user")
         raise HTTPException(status_code=500,detail="internal server error")
      else:
         logger.debug(f"{user.name},{user.role}")
         return user.name
@app.post("/userLogin",status_code=200)
async def LoginUser(LoginUser:UserPost,session:SessionDep):
   statement=select(User).where(User.name==LoginUser.name)
   user=session.exec(statement).first()
   if not user or not unhash_password(LoginUser.hash_pass,user.hash_pass):
      raise HTTPException(status_code=401, detail="Invalid credentials")
   token = create_access_token({"user_id": user.id})
   return {"access_token": token}  

security = HTTPBearer()



def get_user(session:SessionDep,
      token=Depends(security)
             ):
   payload=verify_token(token.credentials)
   if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
   user_id=payload.get('user_id')
   user = session.get(User, user_id)
   if not user:
      raise HTTPException(status_code=404, detail="User not found")

   return user
def AllowedHosts(roles:list[str]):
   def Rolebased(user:User=Depends(get_user)):
      if user.role not in roles:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="take a walk user!"
         )
      return user
   return Rolebased


@app.get("/",response_model=Response[list[Car]])
async def GetCars(session:SessionDep):
  cars=session.exec(select(Car)).all()
  return {"data":cars}

@app.post("/add",status_code=201,response_model=Car)
async def CreateCar(car_data:CarPost,session:SessionDep,user:User=Depends(get_user)):
   try:
    car=Car(
       name=car_data.name,
       hp=car_data.hp,
       model=car_data.model,
       owner_id=user.id

    )
    if car:
        session.add(car)
        session.commit()
        session.refresh(car)
        return car
   except Exception as e:
    print(e)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=str(e))

admin_req=AllowedHosts(["admin"])
@app.put("/update/{id}",status_code=status.HTTP_200_OK,response_model=Car) 
async def UpadteCar(id:int,update_data:CarPost,session:SessionDep,user:User=Depends(admin_req)):  
   car=session.get(Car,id)
   if not car:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="not present in db")
   if user.role!="admin" and car.owner_id!=user.id:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="you are not the user who created this resource")
      
   car.name=update_data.name
   car.hp = update_data.hp
   car.model=update_data.model
   session.add(car)
   session.commit()
   session.refresh(car)
   return car

@app.delete("/delete/{id}",status_code=status.HTTP_204_NO_CONTENT)
async def Deletecar(id:int,session:SessionDep
                    ,user: User = Depends(admin_req)):

      car=session.get(Car,id)
      if not car:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="not present in db")
      
      session.delete(car)
      session.commit()

   