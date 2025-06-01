import torch
from torchvision import transforms
from PIL import Image
import os
import sys
import json
import time
import random
from pathlib import Path

# Importa a função do nosso módulo load_model.py
# Se main.py está em FIAP/src/ e load_model.py está em FIAP/src/model/, esta importação funciona.
from model.load_model import carregar_modelo_incendio

# --- Configurações ---
NUM_CLASSES_PROJETO = (
    2  # Número de classes para o problema (ex: incêndio, não incêndio)
)

# Caminho para o modelo relativo à raiz do projeto (FIAP/)
# Ajuste "saved_models" para "modelos_salvos" se este for o nome da sua pasta.
CAMINHO_MODELO_CHECKPOINT = "saved_models/modelo_incendio.pth"

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
    """
    Carrega uma imagem, aplica transformações e faz uma previsão usando o modelo.

    Args:
        caminho_imagem (str): Caminho para o arquivo de imagem.
        modelo: O modelo PyTorch treinado.
        device: O dispositivo (CPU/CUDA) onde o modelo está.
        transformacoes: As transformações torchvision a serem aplicadas na imagem.
        mapeamento_classes (dict): Dicionário para mapear o índice da classe para um nome.

    Returns:
        str: A descrição da classe prevista, ou None em caso de erro.
    """
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
        print(f"Saídas brutas do modelo: {saida}")  # Linha de depuração
        # Você pode também imprimir as probabilidades após aplicar Softmax
        # probabilidades = torch.softmax(saida, dim=1)
        # print(f"Probabilidades: {probabilidades}")
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

""""
if __name__ == "__main__":
    print("Iniciando script principal...")

    try:
        print(
            f"Carregando modelo com {NUM_CLASSES_PROJETO} classes do checkpoint '{CAMINHO_MODELO_CHECKPOINT}'..."
        )
        modelo_incendio, dispositivo = carregar_modelo_incendio(
            num_classes_saida=NUM_CLASSES_PROJETO,
            caminho_relativo_checkpoint=CAMINHO_MODELO_CHECKPOINT,
        )
        print(f"Modelo carregado com sucesso no dispositivo: {dispositivo}!")
    except Exception as e:
        print(f"Falha crítica ao carregar o modelo: {e}")
        exit()

    script_main_dir = os.path.dirname(os.path.abspath(__file__))  # FIAP/src/
    project_root_dir = os.path.join(script_main_dir, "..")  # FIAP/
    caminho_imagem_exemplo = os.path.join(
        project_root_dir, "data", "test_images", "img6.jpg"
    )
    caminho_imagem_exemplo = os.path.normpath(caminho_imagem_exemplo)

    print(f"\nTentando fazer previsão para a imagem: {caminho_imagem_exemplo}")
    descricao_previsao = prever_imagem(
        caminho_imagem_exemplo,
        modelo_incendio,
        dispositivo,
        transformacoes_imagem,
        MAPEAMENTO_CLASSES,
    )

    if descricao_previsao:
        print(f"Resultado da previsão: {descricao_previsao}")

    print("\nScript principal concluído.")
"""