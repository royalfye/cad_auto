from datetime import datetime, timedelta
import pandas as pd
from typing import List
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

def calcular_ala_atual(data_alvo: datetime) -> int:
    """
    Calcula qual ala (1, 2, 3 ou 4) está de plantão.
    Baseado na âncora: 21/03/2026 às 07:45 inicia a 4ª Ala.
    """
    # 1. Âncora de referência
    referencia_data = datetime(2026, 3, 21, 7, 45)
    referencia_ala = 4
    
    # 2. Ajuste de Turno: Subtraímos 7h45 para que o dia "vire" apenas às 07:45
    # Ex: Se são 07:00 da manhã, o cálculo considerará como se ainda fosse o dia anterior.
    atraso_turno = timedelta(hours=7, minutes=45)
    data_ajustada = data_alvo - atraso_turno
    ref_ajustada = referencia_data - atraso_turno
    
    # 3. Diferença de dias inteiros
    diferenca_dias = (data_ajustada.date() - ref_ajustada.date()).days
    
    # 4. Cálculo do Ciclo de 4 alas (Aritmética Modular)
    # (Ref + dias) % 4 nos dá a posição no ciclo de 0 a 3, somamos 1 para virar 1 a 4.
    ala = (referencia_ala - 1 + diferenca_dias) % 4 + 1
    
    return ala

def obter_nome_grupo_whatsapp(ala_texto: str) -> str:
    """
    Retorna o nome exato do grupo no WhatsApp com base na ala selecionada.
    Ex: '4ª ALA' -> '4ª Ala - Ocorrências'
    """
    mapeamento = {
        "1ª ALA": "1ª Ala - Ocorrências",
        "2ª ALA": "2ª Ala - Ocorrências",
        "3ª ALA": "3ª Ala - Ocorrências",
        "4ª ALA": "4ª Ala - Ocorrências",
    }
    return mapeamento.get(ala_texto, "Grupo de Ocorrências")