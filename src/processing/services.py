from typing import List
# Note que importamos o models da pasta processing
from src.processing.models import Ocorrencia 

def converter_dataframe_para_objetos(df) -> List[Ocorrencia]:
    """Transforma o DataFrame da Silver em objetos Ocorrencia."""
    ocorrencias = []
    if df is None:
        return []
        
    for linha in df.itertuples(index=False):
        obj = Ocorrencia(
            id_chamada=str(linha.call_id),
            natureza=linha.nature,
            horario=linha.created_at,
            endereco=linha.address,
            unidade=linha.unit,
            status=linha.status,
            status_icone=linha.status_indicator
        )
        ocorrencias.append(obj)
    return ocorrencias