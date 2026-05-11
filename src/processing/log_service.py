from pathlib import Path

# Definimos o caminho relativo ao projeto
LOG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "disparados.log"

def ocorrencia_ja_disparada(call_id):
    """Verifica se o ID da chamada já consta no arquivo de log."""
    if not LOG_PATH.exists():
        return False
    with open(LOG_PATH, "r") as f:
        ids_enviados = f.read().splitlines()
    return str(call_id) in ids_enviados

def registrar_disparo(call_id):
    """Salva o ID da chamada no arquivo de log."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(f"{call_id}\n")