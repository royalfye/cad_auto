import pandas as pd
import logging
from pathlib import Path
from typing import Optional

# Log config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataProcessor:
    """
    Responsável por transformar dados brutos (Bronze) em dados limpos (Silver).
    """
    
    def __init__(self):

        self.root = Path(__file__).resolve().parent.parent.parent
        
        self.bronze_path = self.root / "data" / "01_bronze"
        self.path_bronze_active = self.bronze_path / "active"
        self.path_bronze_historical = self.bronze_path / "historical"
        
        self.path_silver = self.root / "data" / "02_silver"
        
        self.column_map = {
            "Nº chamada": "call_id",
            "Data/hora de criação": "created_at",
            "Local do fato": "address",
            "Natureza": "nature",
            "Unidade Responsável": "unit",
            "Situação": "status",
            "Data/hora da situação atual": "updated_at"
        }
    
        self.path_bronze_active.mkdir(parents=True, exist_ok=True)
        self.path_bronze_historical.mkdir(parents=True, exist_ok=True)
        self.path_silver.mkdir(parents=True, exist_ok=True)

    def process_latest_active_call(self) -> Optional[pd.DataFrame]:

        # 1. Locate the files
        files = list(self.path_bronze_active.glob("*.csv"))
        if not files:
            logging.warning("Nenhum arquivo CSV encontrado em 01_bronze/active")
            return None
        
        # 2. Get the most recent file
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        logging.info(f"Processando arquivo mais recente: {latest_file.name}")

        try:
            # 3. Reading
            df = pd.read_csv(latest_file, sep=';', encoding='latin1', on_bad_lines='skip')
            
            # 4. Selection and renaming
            existing_cols = [c for c in self.column_map.keys() if c in df.columns]
            df_silver = df[existing_cols].rename(columns=self.column_map)

            # 5. Filter to remove the lines with 'status': 'Classificada'
            if 'status' in df_silver.columns:
                df_silver = df_silver[df_silver['status'] != 'Classificada'].copy()

            # 6. Filter to only keep the lines with 'Passos' in the 'unit' column
            if 'unit' in df_silver.columns:
                # O case=False garante que ele ache "PASSOS", "Passos" ou "passos"
                # O na=False evita erros caso existam células vazias
                df_silver = df_silver[df_silver['unit'].str.contains('PASSOS', case=False, na=False)].copy()

           # 7. Real date convertion
            for col in ['created_at', 'updated_at']:
                if col in df_silver.columns:
                    df_silver[col] = pd.to_datetime(df_silver[col], dayfirst=True, errors='coerce')

            # 8. Organization: Older on the top
            if 'status' in df_silver.columns and 'created_at' in df_silver.columns:
                # 8.1. Active:0 --- Finished:1
                df_silver['is_finished'] = (df_silver['status'] == 'Terminada').astype(int)

                # 8.2. Organization:
                # is_finished: True (0 before 1) -> Active calls firt
                # created_at: True (Older before the recent) -> 14:15 before 14:30
                df_silver = df_silver.sort_values(
                    by=['is_finished', 'created_at'], 
                    ascending=[True, True] 
                )

                # 8.3. Remove the auxiliar column
                df_silver = df_silver.drop(columns=['is_finished'])

            # 9. Brazilian format
            for col in ['created_at', 'updated_at']:
                if col in df_silver.columns:
                    df_silver[col] = df_silver[col].dt.strftime('%d/%m/%Y %H:%M:%S')

            # 10. Nature column cleaning
            if 'nature' in df_silver.columns:
                df_silver['nature'] = df_silver['nature'].str.split('(').str[0].str.strip()

            # 11. call_id cleaning
            if 'call_id' in df_silver.columns:
                df_silver['call_id'] = df_silver['call_id'].astype(str).str.replace(r'\D', '', regex=True)

            # 12: Status column
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
                # set '🔴' as default for status that are not in the map
                icons = df_silver['status'].apply(lambda x: status_map.get(x, '🔴'))
                df_silver.insert(0, 'status_indicator', icons)

            # 13. Save on silver
            output_path = self.path_silver / "active_calls_summary.csv"
            # encoding utf-8-sig
            df_silver.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            logging.info(f"Sucesso! Dados salvos em: {output_path}")
            return df_silver

        except Exception as e:
            logging.error(f"Falha ao processar dados: {e}")
            return None

# Block test
if __name__ == "__main__":
    processor = DataProcessor()
    resultado = processor.process_latest_active_call()
    if resultado is not None:
        print("\n--- Prévia dos Dados Processados ---")
        print(resultado.head())