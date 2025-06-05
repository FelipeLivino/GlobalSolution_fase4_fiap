from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from typing import List
from src.db.models import SensorsData, SuccessResponse, FileUploadResponse
import shutil
import os
from src.model.main_model import perform_ai_magic, perform_ai_sensors

app = FastAPI()


@app.post("/prediction/sensor", response_model=SuccessResponse)
async def prediction(data: SensorsData):
    """
    Recebe dados JSON via POST e retorna uma mensagem de sucesso.
    """
    print("Dados JSON recebidos:")
    print(f"  dados: {data.dados}")
    previsoes = perform_ai_sensors(data.dados)

    response_data = {
        "message": previsoes
    }
    return response_data


@app.post("/prediction/img", response_model=FileUploadResponse)
async def prediction_img(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")

    print(f"Arquivo recebido: {file.filename}")
    print(f"Tipo de conteúdo do arquivo: {file.content_type}")

    # Validação básica do tipo de arquivo 
    allowed_content_types = ["image/jpeg", "image/jpg"] 
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo inválido: {file.content_type}. Esperado: {', '.join(allowed_content_types)}"
        )

    file_path = os.path.join("data", "upload",file.filename)
    file_path = os.path.normpath(file_path)

    #Salvar Arquivo
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"Arquivo salvo em: {file_path}")
        saved = True
    except Exception as e:
        print(f"Erro ao salvar o arquivo: {e}")
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar o arquivo: {e}")

    #Realizar predição
    prediction_result = perform_ai_magic(file_path)

    return {
        "message": prediction_result.get("message", "Erro ao obter mensagem da previsão")
    }

