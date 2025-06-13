from click import prompt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI
from typing import Literal 
import json

import config
from config import settings
from functools import lru_cache


class Customer(BaseModel):
    id: str
    name: str

class TransactionEvent(BaseModel):
    id: str
    action: Literal["CREATE", "UPDATE", "DELETE", "READ"] # Exemplo, ajuste conforme necessário
    timestamp: str # Ou datetime, se preferir fazer a validação/conversão
    customer: Customer
    userAgent: str = Field(alias="userAgent")
    path: str
    accessTime: str = Field(alias="accessTime") # Ou datetime
    ipAddress: str = Field(alias="ipAddress")
    sessionId: str = Field(alias="sessionId")
    status: Literal["SUCCESS", "FAILURE", "PENDING"] # Exemplo, ajuste conforme necessário
    httpMethod: Literal["POST", "GET", "PUT", "DELETE", "PATCH"] = Field(alias="httpMethod")

def send_analysis(txt: str):

    headers = {"Content-Type": "application/json"}
    data = {"input": txt}
    response = headers + data
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")


context_instructions = (
    "Você é um agente de I.A especializado em detecção de fraude bancária. "
    "Analise o seguinte evento de transação bancária recebido em formato JSON:\n\n"
    "Sua tarefa é avaliar se a ação representa uma possível fraude. "
    "Responda estritamente no formato JSON abaixo, sem explicações adicionais:\n\n"
    "{isValid:bool, Probability:float}\n\n"
    "Onde:\n"
    "- isValid deve ser true se a ação for legítima, ou false se for suspeita de fraude.\n"
    "- Probability é um valor entre 0 e 100 indicando a probabilidade de fraude.\n"
    "Verifique inconsistencias, padrões suspeitos e qualquer outro sinal de alerta.\n\n"
    "Exemplo de resposta:\n"
    "{isValid:false, Probability:87}\n\n"
)

app = FastAPI()


@lru_cache
def get_settings():
    return config.Settings()


@app.get("/info")
async def root():
    return {"message": "API de Análise de Fraude Bancária", "version": "1.0"}


@app.post("/analysis/")
async def fraud_analysis(event: TransactionEvent):
    client = OpenAI(api_key=settings.openai_api_key)

    event_json_string = event.model_dump_json()
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Ou o modelo que você estiver usando, ex: "gpt-4.1" não é um nome comum, verifique a documentação
            messages=[
                {"role": "system", "content": context_instructions},
                # Passamos o evento JSON como conteúdo do usuário
                {"role": "user", "content": event_json_string}
            ],
            # Se o modelo suportar e for instruído a retornar JSON diretamente:
            # response_format={"type": "json_object"} # Para modelos mais recentes que suportam JSON mode
        )
        
        analysis_result_content = response.choices[0].message.content
        
        # Tentar parsear o resultado JSON da OpenAI
        try:
            parsed_result = json.loads(analysis_result_content)
            return parsed_result
        except json.JSONDecodeError:
            # Se não for um JSON válido, pode ser um erro ou uma resposta inesperada
            print(f"OpenAI response was not valid JSON: {analysis_result_content}")
            raise HTTPException(status_code=500, detail="Invalid response format from analysis model")

    except Exception as e:
        print(f"Error calling OpenAI API or processing response: {e}")
        raise HTTPException(status_code=500, detail="Error during fraud analysis")

    return response.choices[0].message.content

