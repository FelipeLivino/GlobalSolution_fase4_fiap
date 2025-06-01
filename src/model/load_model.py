import sys
import torch
import os
import torchvision.models as models


def carregar_modelo_incendio(
    num_classes_saida: int,
    caminho_relativo_checkpoint: str = "saved_models/modelo_incendio.pth",
):

    # 1. Crie uma nova instância do ResNet-18.
    #    Usamos weights=None. Por padrão, models.resnet18(weights=None)
    #    terá uma camada 'fc' com 1000 classes de saída.
    modelo = models.resnet18(weights=None)

    # 2. Defina o dispositivo
    if torch.cuda.is_available():
        device_name = "cuda"
    elif sys.platform == "darwin" and torch.backends.mps.is_available():
        device_name = "mps"
    else:
        device_name = "cpu"
    device = torch.device(device_name)
    modelo.to(device)

    # 3. Construa o caminho absoluto para o arquivo de checkpoint
    script_dir = os.path.dirname(
        os.path.abspath(__file__)
    )  # Ex: c:\Users\felip\FIAP\src\model
    project_root = os.path.join(script_dir, "..", "..")  # Ex: c:\Users\felip\FIAP

    path_checkpoint_absoluto = os.path.join(project_root, caminho_relativo_checkpoint)
    path_checkpoint_absoluto = os.path.normpath(path_checkpoint_absoluto)

    if not os.path.exists(path_checkpoint_absoluto):
        raise FileNotFoundError(
            f"Arquivo de checkpoint não encontrado em: {path_checkpoint_absoluto}"
        )

    # 4. Carregue os pesos salvos.
    print(
        f"Tentando carregar checkpoint de: {path_checkpoint_absoluto} para o dispositivo {device_name}"
    )
    # Carregue os pesos. Neste ponto, 'modelo' tem uma camada fc para 1000 classes,
    # que deve corresponder ao checkpoint 'modelo_incendio.pth' conforme o erro.
    modelo.load_state_dict(torch.load(path_checkpoint_absoluto, map_location=device))
    print("Checkpoint carregado com sucesso.")

    # 5. Agora, modifique a camada final (fc) para o número desejado de classes.
    #    As camadas convolucionais (anteriores à fc) terão os pesos carregados do checkpoint.
    #    Esta nova camada fc será inicializada com pesos aleatórios e precisará ser treinada (fine-tuning).
    num_ftrs = modelo.fc.in_features
    modelo.fc = torch.nn.Linear(num_ftrs, num_classes_saida)
    modelo.to(device)  # Mover para o dispositivo novamente após modificar a camada

    # 6. Coloque o modelo em modo de avaliação
    modelo.eval()

    print(
        f"Modelo ResNet-18 configurado para {num_classes_saida} classes, carregado de '{path_checkpoint_absoluto}' e pronto para inferência no dispositivo '{device}'."
    )
    return modelo, device  # Retorna o objeto torch.device
