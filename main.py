from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import Depends, Header, HTTPException
from sqlmodel import Field, SQLModel, Session, create_engine, select,text
from typing import Optional
from passlib.context import CryptContext
from fastapi import Body



engine = create_engine("mysql+pymysql://root:Alinapauly304@localhost:3306/itemtodo")

app=FastAPI()


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(SQLModel,table=True):
    item_id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    isdone:bool=False




class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: str

   
SQLModel.metadata.create_all(engine)

from jose import JWTError, jwt
from datetime import datetime, timedelta

# 🔑 Secret key (keep this safe)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ✅ Create JWT token
def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})  # set expiry time
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 🔍 Decode JWT token
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None




pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)



@app.post("/register")
def register(username: str = Body(...), password: str = Body(...), role: str = "user"):
    with Session(engine) as session:
        # Check if user exists
        existing = session.exec(select(User).where(User.username == username)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        user = User(
            username=username,
            hashed_password=hash_password(password),
            role=role
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"message": "User registered", "username": user.username, "role": user.role}

@app.post("/login")
def login(username: str = Body(...), password: str = Body(...)):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_token({"sub": user.username, "role": user.role})
        return {"access_token": token, "token_type": "bearer"}


def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]  # Extract token from 'Bearer <token>'
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": payload["sub"], "role": payload["role"]}
    except:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
@app.post("/items")
def additem(item:Item):
    with Session(engine) as session:
        session.add(item)
        session.commit()
        session.refresh(item)
    return item

@app.get("/items/{item_id}",response_model=Item)
def getitem(item_id:int)->Item:
    with Session(engine) as session:
        item = session.get(Item,item_id)
        return item

@app.get("/items}",response_model=Item)
def getitem(item_id:int)->Item:
    with Session(engine) as session:
        items = session.exec(select(Item)).all()
        return items 
       
@app.get("/items", response_model=list[Item])
def get_items(limit: int = 5):
    with Session(engine) as session:
        item = session.exec(select(Item).limit(limit)).all()
        return item


@app.put("/status", response_model=Item)
def updatestatus(item: Item):
    with Session(engine) as session:
        stored_item = session.get(Item, item.item_id)

        if not stored_item:
            raise HTTPException(status_code=404, detail="Item not found")

       
        stored_item.text = item.text
        stored_item.isdone = item.isdone

        session.add(stored_item)
        session.commit()
        session.refresh(stored_item)
        return stored_item

def require_role(allowed_roles: list[str]):
    def checker(user=Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        return user
    return checker

def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]  # Extract token from 'Bearer <token>'
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": payload["sub"], "role": payload["role"]}
    except:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    


@app.delete("/deletebyid/{item_id}")
def deletebyid(item_id:int, user=Depends(require_role(["admin"]))):
    with Session(engine) as session:
        stored_item = session.get(Item,item_id)
        session.delete(stored_item)
        session.commit()
        return {"item deleted"}


@app.delete("/delete/{text}")
def deletebytext(text:str):
    with Session(engine) as session:
        stored_item = session.exec(select(Item).where(Item.text==text)).first()
        print(stored_item)
        session.delete(stored_item)
        session.commit()
        return {"item deleted"}



        