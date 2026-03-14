import pandas as pd
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

def generate_activity_report(df: pd.DataFrame) -> str:
    """
    Takes the Silver DataFrame and generates the formatted activity summary.
    """
    if df is None or df.empty:
        return "Nenhuma ocorrência ativa encontrada para o relatório."

    # 1. Contagem baseada na primeira letra da coluna 'nature'
    # O .value_counts() faz o trabalho pesado de contar
    counts = df['nature'].astype(str).str[0].value_counts().sort_index()

    # 2. Montagem do texto (Idêntico ao seu objetivo)
    report_lines = [
        "Período de 07:45(d) até 07:45 (d+1)\n"
    ]

    for char, count in counts.items():
        report_lines.append(f"{char} - {count}")

    # 3. Rodapé
    total = counts.sum()
    report_lines.append(f"\nTOTAL - {total}")

    return "\n".join(report_lines)