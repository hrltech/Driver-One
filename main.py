import os
from datetime import datetime
from typing import Literal
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import h3
from supabase import create_client, Client

app = FastAPI(
    title="API Dinâmico Driver One",
    description="API FastAPI para registro de dados de tarifa dinâmica (Uber/99) com integração H3 e Supabase.",
    version="1.0.0"
)

# Inicialização do cliente Supabase a partir das variáveis de ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class DinamicoRequest(BaseModel):
    latitude: float = Field(..., description="Latitude do local", example=-23.550520)
    longitude: float = Field(..., description="Longitude do local", example=-46.633308)
    plataforma: Literal["uber", "99"] = Field(..., description="Plataforma de transporte ('uber' ou '99')", example="uber")
    valor_dinamico: float = Field(..., description="Multiplicador ou valor do dinâmico", example=1.5)


@app.get("/")
def read_root():
    return {"status": "online", "service": "Driver One Dinâmico API"}


@app.post("/api/v1/dinamico", status_code=status.HTTP_201_CREATED)
def criar_registro_dinamico(payload: DinamicoRequest):
    try:
        # Converter latitude e longitude para o índice H3 na resolução 8
        h3_index = h3.latlng_to_cell(payload.latitude, payload.longitude, 8)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao calcular o índice H3: {str(e)}"
        )

    # Obter data/hora atual em UTC (ou local conforme padrão desejado)
    now = datetime.utcnow()
    dia_semana = now.weekday()  # 0 (Segunda-feira) a 6 (Domingo)
    hora_registo = now.time().isoformat()  # Formato 'HH:MM:SS.ffffff' ou string ISO

    dados_insercao = {
        "h3_index": h3_index,
        "plataforma": payload.plataforma,
        "valor_dinamico": payload.valor_dinamico,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "dia_semana": dia_semana,
        "hora_registo": hora_registo
    }

    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credenciais do Supabase não configuradas no servidor."
        )

    try:
        response = supabase.table("registos_dinamico").insert(dados_insercao).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao inserir dados no Supabase: {str(e)}"
        )

    return {
        "message": "Registro dinâmico criado com sucesso",
        "h3_index": h3_index,
        "data": dados_insercao
    }
