import sys
import torch
import os
import torchvision.models as models
import joblib

def carregar_modelo_incendio(
    num_classes_saida: int,
    caminho_relativo_checkpoint: str = "saved_models/modelo_incendio.pth",
):
    # 1. Cria uma nova instância do ResNet-18.
    modelo = models.resnet18(weights=None)

    # 2. Define o dispositivo
    if torch.cuda.is_available():
        device_name = "cuda"
    elif sys.platform == "darwin" and torch.backends.mps.is_available():
        device_name = "mps"
    else:
        device_name = "cpu"
    device = torch.device(device_name)
    modelo.to(device)

    # 3. Constroi o caminho absoluto para o arquivo de checkpoint
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

    path_checkpoint_absoluto = os.path.join(project_root, caminho_relativo_checkpoint)
    path_checkpoint_absoluto = os.path.normpath(path_checkpoint_absoluto)

    if not os.path.exists(path_checkpoint_absoluto):
        raise FileNotFoundError(
            f"Arquivo de checkpoint não encontrado em: {path_checkpoint_absoluto}"
        )

    # 4. Carregando os pesos salvos.
    print(
        f"Tentando carregar checkpoint de: {path_checkpoint_absoluto} para o dispositivo {device_name}"
    )

    # Carrega os pesos
    modelo.load_state_dict(torch.load(path_checkpoint_absoluto, map_location=device))
    print("Checkpoint carregado com sucesso.")

    # 5. Modificando a camada final (fc) para o número desejado de classes.
    num_ftrs = modelo.fc.in_features
    modelo.fc = torch.nn.Linear(num_ftrs, num_classes_saida)
    modelo.to(device)  

    # 6. Modelo em modo de avaliação
    modelo.eval()

    print(
        f"Modelo ResNet-18 configurado para {num_classes_saida} classes, carregado de '{path_checkpoint_absoluto}' e pronto para inferência no dispositivo '{device}'."
    )
    return modelo, device  # Retorna o objeto torch.device


def carregar_modelo_sensores(
    caminho_relativo_checkpoint: str = "saved_models/svm_model.joblib",
    caminho_relativo_scaler: str = "saved_models/scaler_sensores.joblib",
):
    #Preparar arquivo
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    path_checkpoint_absoluto = os.path.join(project_root, caminho_relativo_checkpoint)
    path_checkpoint_absoluto = os.path.normpath(path_checkpoint_absoluto)

    # Lógica similar para o scaler:
    project_root_scaler = os.path.abspath(os.path.join(script_dir, "..", "..")) # Ajuste conforme sua estrutura
    path_scaler_absoluto = os.path.join(project_root_scaler, caminho_relativo_scaler)
    path_scaler_absoluto = os.path.normpath(path_scaler_absoluto)

    #carregar o modelo
    modelo_carregado = joblib.load(path_checkpoint_absoluto)
    scaler_carregado = joblib.load(path_scaler_absoluto)

    return modelo_carregado, scaler_carregado