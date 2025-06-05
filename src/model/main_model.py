import torch
from torchvision import transforms
from PIL import Image
import numpy as np 

# Importa a função do nosso módulo load_model.py
from .load_model import carregar_modelo_incendio, carregar_modelo_sensores

# --- Configurações ---
NUM_CLASSES_PROJETO = 2

CORRESPONDENCIA_CLASSES_SENSORES = {0: "ALERTA MAXIMO", 1: "ALTO", 2: "ATENCAO", 3: "NORMAL"}

# Caminho para o modelo relativo à raiz do projeto 
# Ajuste "saved_models" para "modelos_salvos" se este for o nome da sua pasta.
CAMINHO_MODELO_CHECKPOINT = "saved_models/modelo_incendio.pth"
CAMINHO_MODELO_Sensores = "saved_models/RandomForest_Optimized_model.joblib"
CAMINHO_SCALER_SENSORES = "saved_models/scaler_sensores.joblib"

# Defina as transformações da imagem (devem ser as mesmas usadas durante o treinamento)
transformacoes_imagem = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

# Mapeamento de classes para nomes legíveis (ajuste conforme seu treinamento)
MAPEAMENTO_CLASSES = {0: "Não Incêndio", 1: "Incêndio"}
# --- Fim das Configurações ---


def prever_imagem(
    caminho_imagem: str, modelo, device, transformacoes, mapeamento_classes
):
    try:
        imagem = Image.open(caminho_imagem).convert("RGB")
    except FileNotFoundError:
        print(f"Erro: Imagem não encontrada em {caminho_imagem}")
        return None
    except Exception as e:
        print(f"Erro ao abrir a imagem {caminho_imagem}: {e}")
        return None

    imagem_tensor = transformacoes(imagem).unsqueeze(0).to(device)

    # Dentro de prever_imagem em main.py
    with torch.no_grad():
        saida = modelo(imagem_tensor)
        print(f"Saídas brutas do modelo: {saida}") 
        _, predicao_idx = torch.max(saida, 1)

    classe_prevista_idx = predicao_idx.item()
    descricao_classe = mapeamento_classes.get(
        classe_prevista_idx, f"Classe Desconhecida ({classe_prevista_idx})"
    )
    return descricao_classe

def perform_ai_magic(image_path_str: str):

    modelo_incendio, dispositivo = carregar_modelo_incendio(
        num_classes_saida=NUM_CLASSES_PROJETO,
        caminho_relativo_checkpoint=CAMINHO_MODELO_CHECKPOINT,
    )
    descricao_previsao = prever_imagem(
        image_path_str,
        modelo_incendio,
        dispositivo,
        transformacoes_imagem,
        MAPEAMENTO_CLASSES,
    )

    if descricao_previsao:
        print(f"Resultado da previsão: {descricao_previsao}")
        return {
            "message": descricao_previsao
        }
    else:
        return {
            "message": "Erro na previsão",
            "error": "Modelo de IA falhou ao processar"
        }
    
#Prever dados dos sensores
def perform_ai_sensors(X_novo_lista):
    X_novo_numpy = np.array(X_novo_lista)
    modelo, scaler = carregar_modelo_sensores(CAMINHO_MODELO_Sensores, CAMINHO_SCALER_SENSORES)
    
    if modelo is None or scaler is None:
        print("Modelo ou scaler não carregado. Abortando predição.")
        return [] # Ou levante uma exceção

    X_novo_numpy = np.array(X_novo_lista)

    # O scaler espera dados 2D. Se X_novo_numpy for 1D (uma única amostra), redimensione.
    if X_novo_numpy.ndim == 1:
        X_novo_numpy = X_novo_numpy.reshape(1, -1)
    
    # Aplicar o escalonamento aos novos dados
    X_novo_scaled = scaler.transform(X_novo_numpy)
    
    previsoes = modelo.predict(X_novo_scaled)
    print(f"Previsões para os novos dados (escalonados): {previsoes}")

    respostas = []
    for elemento in previsoes:
        respostas.append(CORRESPONDENCIA_CLASSES_SENSORES.get(elemento, "Classe Desconhecida"))
    return respostas