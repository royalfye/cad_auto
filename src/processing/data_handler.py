import pandas as pd
import logging
from pathlib import Path
from typing import Optional

# Configuração de logs para sabermos o que o robô está fazendo
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataProcessor:
    """
    Responsável por transformar dados brutos (Bronze) em dados limpos (Silver).
    """
    
    def __init__(self):
        # 1. Define a Raiz do Projeto
        self.root = Path(__file__).resolve().parent.parent.parent
        
        # 2. Define a estrutura Medalhão (Bronze -> Silver)
        # Criamos a bronze_path como base para evitar o erro de AttributeError
        self.bronze_path = self.root / "data" / "01_bronze"
        self.path_bronze_active = self.bronze_path / "active"
        self.path_bronze_historical = self.bronze_path / "historical"
        
        self.path_silver = self.root / "data" / "02_silver"
        
        # 3. Mapeamento de colunas (Mantido conforme seu padrão)
        self.column_map = {
            "Nº chamada": "call_id",
            "Data/hora de criação": "created_at",
            "Local do fato": "address",
            "Natureza": "nature",
            "Unidade Responsável": "unit",
            "Situação": "status",
            "Data/hora da situação atual": "updated_at"
        }
        
        # 4. Garante que TODA a estrutura de pastas exista
        # Isso evita erros de "Pasta não encontrada" na primeira execução
        self.path_bronze_active.mkdir(parents=True, exist_ok=True)
        self.path_bronze_historical.mkdir(parents=True, exist_ok=True)
        self.path_silver.mkdir(parents=True, exist_ok=True)

    def process_latest_active_call(self) -> Optional[pd.DataFrame]:
        """
        Lê o arquivo mais recente da pasta 'active' e limpa os dados.
        """
        # 1. Localizar arquivos
        files = list(self.path_bronze_active.glob("*.csv"))
        if not files:
            logging.warning("Nenhum arquivo CSV encontrado em 01_bronze/active")
            return None
        
        # 2. Pegar o arquivo mais recente (pela data de modificação)
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        logging.info(f"Processando arquivo mais recente: {latest_file.name}")

        try:
            # 3. Leitura
            df = pd.read_csv(latest_file, sep=';', encoding='latin1', on_bad_lines='skip')
            
            # 4. Seleção e Renomeação
            existing_cols = [c for c in self.column_map.keys() if c in df.columns]
            df_silver = df[existing_cols].rename(columns=self.column_map)

            # 5. Limpeza de Tipos
            # Datas
            for col in ['created_at', 'updated_at']:
                if col in df_silver.columns:
                    df_silver[col] = pd.to_datetime(df_silver[col], dayfirst=True, errors='coerce')

            # Limpeza da Natureza (Removendo o que vem após o parêntese)
            if 'nature' in df_silver.columns:
                df_silver['nature'] = df_silver['nature'].str.split('(').str[0].str.strip()

            # Limpar o ID da chamada
            if 'call_id' in df_silver.columns:
                df_silver['call_id'] = df_silver['call_id'].astype(str).str.replace(r'\D', '', regex=True)

            # --- NOVA COLUNA DE ÍCONES (À ESQUERDA) ---
            if 'status' in df_silver.columns:
                status_map = {
                    'Atribuída ao órgão': '🟢',
                    'No local': '🔴',
                    'Em controle': '⚪',
                    'Terminada': '⚫',
                    'À caminho': '🔵',
                    'Despachada': '🟡',
                    'Em retorno': '🟠'
                }
                # .get permite definir o padrão '🔴' caso o status não esteja na lista
                icons = df_silver['status'].apply(lambda x: status_map.get(x, '🔴'))
                df_silver.insert(0, 'status_indicator', icons)

            # 6. Salvar na Silver
            output_path = self.path_silver / "active_calls_summary.csv"
            # Importante: salvar com encoding utf-8-sig para os emojis aparecerem no Excel
            df_silver.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            logging.info(f"Sucesso! Dados salvos em: {output_path}")
            return df_silver

        except Exception as e:
            logging.error(f"Falha ao processar dados: {e}")
            return None

# Bloco de teste: Só roda se você executar este arquivo diretamente
if __name__ == "__main__":
    processor = DataProcessor()
    resultado = processor.process_latest_active_call()
    if resultado is not None:
        print("\n--- Prévia dos Dados Processados ---")
        print(resultado.head())