from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from config import settings
from functools import lru_cache

class Prompt(BaseModel):
    input:str

app = FastAPI()

@lru_cache
def get_settings():
    return config.Settings()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.post("/items/")
async def create_item(prompt:Prompt):
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.responses.create(
        model="gpt-4.1",
        input=prompt.input
    )

    return response.output_text