from fastapi import FastAPI
from pydantic import BaseModel


class Item(BaseModel):
    name:str
    decription:str

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.post("/items/")
async def create_item(item:Item):

    return item