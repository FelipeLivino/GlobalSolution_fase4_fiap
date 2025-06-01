# /full/path/to/your/project/api.py
import shutil
import subprocess
import json
import uuid
import sys
from pathlib import Path
import logging
import asyncio

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager


# --- Configuração de Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuração de Caminhos ---
# Assume que api.py e main_model.py estão no mesmo diretório.
# A pasta 'data/test_images' será criada dentro deste diretório.
BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "data" / "test_images"
MODEL_SCRIPT = BASE_DIR / "main_model.py"

# Cria uma instância da aplicação FastAPI
app = FastAPI(title="API de Processamento de Imagens com IA")

# --- Evento de Inicialização ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Cria o diretório de armazenamento de imagens se ele não existir.
    """
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Diretório de armazenamento de imagens: {IMAGE_DIR}")
    if not MODEL_SCRIPT.exists():
        logger.warning(f"ATENÇÃO: Script do modelo não encontrado em {MODEL_SCRIPT}. As predições falharão.")
    elif not MODEL_SCRIPT.is_file():
        logger.warning(f"ATENÇÃO: O caminho do script do modelo {MODEL_SCRIPT} não é um arquivo. As predições falharão.")

# --- Endpoint da API ---
@app.post("/predict/")
async def upload_image_and_predict(image: UploadFile = File(...)):
    """
    Recebe uma imagem, salva, chama o script do modelo de IA e retorna a predição.
    """
    # Validação básica do tipo de arquivo (pode ser mais robusta)
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Tipo de arquivo inválido. Apenas imagens são permitidas.")

    # Gera um nome de arquivo único para evitar sobrescritas e lidar com caracteres especiais.
    # Usa a extensão original para clareza, mas garante que seja segura.
    original_filename = Path(image.filename)
    extension = original_filename.suffix.lower() if original_filename.suffix else ".png" # Extensão padrão
    
    # Lista de extensões de imagem permitidas (exemplo)
    allowed_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
    if extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Extensão de arquivo não suportada: {extension}. Permitidas: {allowed_extensions}")

    unique_filename = f"{uuid.uuid4()}{extension}"
    file_location = IMAGE_DIR / unique_filename

    logger.info(f"Tentando salvar imagem enviada para: {file_location}")

    # Salva a imagem enviada
    try:
        # Para arquivos grandes, considere operações de arquivo assíncronas com aiofiles
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        logger.info(f"Imagem '{image.filename}' salva como '{unique_filename}' em {file_location}")
    except Exception as e:
        logger.error(f"Falha ao salvar imagem {image.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Não foi possível salvar a imagem: {e}")
    finally:
        # É crucial fechar o arquivo enviado
        await image.close()

    # Verifica se o script do modelo existe antes de tentar executá-lo
    if not MODEL_SCRIPT.exists() or not MODEL_SCRIPT.is_file():
        logger.error(f"Script do modelo de IA não encontrado ou não é um arquivo: {MODEL_SCRIPT}")
        raise HTTPException(status_code=500, detail="Script do modelo de IA não configurado ou não encontrado.")

    logger.info(f"Chamando script do modelo de IA: {MODEL_SCRIPT} com imagem: {file_location}")

    # Executa o script main_model.py como um subprocesso
    try:
        # Usando sys.executable para garantir o interpretador Python correto
        # Passa o caminho absoluto para o script do modelo e arquivo de imagem para robustez
        cmd = [sys.executable, str(MODEL_SCRIPT.resolve()), str(file_location.resolve())]
        logger.info(f"Executando comando: {' '.join(cmd)}")

        loop = asyncio.get_event_loop()
        process = await loop.run_in_executor(
            None,  # Usa o executor de thread pool padrão
            lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False, # Verificaremos o returncode manualmente
                cwd=BASE_DIR # Define o diretório de trabalho se o script do modelo tiver dependências de caminho relativo
            )
        )

        if process.returncode != 0:
            error_message = f"Execução do script do modelo de IA falhou com código de retorno {process.returncode}."
            if process.stderr:
                error_message += f" Erro: {process.stderr.strip()}"
            logger.error(error_message)
            raise HTTPException(status_code=500, detail=error_message)

        # Analisa a saída JSON do script
        try:
            model_result = json.loads(process.stdout)
            logger.info(f"Saída do script do modelo de IA: {model_result}")
        except json.JSONDecodeError:
            logger.error(f"Falha ao analisar saída JSON do script do modelo de IA. Saída: {process.stdout}")
            raise HTTPException(status_code=500, detail="Script do modelo de IA retornou saída não-JSON.")

        return JSONResponse(content=model_result)

    except FileNotFoundError: # Para sys.executable ou MODEL_SCRIPT se os caminhos estiverem errados
        logger.error(f"Erro: Interpretador Python ou script do modelo não encontrado. Verifique os caminhos.")
        raise HTTPException(status_code=500, detail="Erro de configuração do servidor: executor do script não encontrado.")
    except Exception as e:
        logger.error(f"Um erro inesperado ocorreu durante o processamento do modelo: {e}")
        raise HTTPException(status_code=500, detail=f"Um erro inesperado ocorreu: {str(e)}")