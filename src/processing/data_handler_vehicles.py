import pandas as pd
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

print("ARQUIVO EXECUTADO")

# Configuração do log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

MAX_ACTIVE_DAYS = 30

class VehicleDataProcessor:
    """
    Responsável por criar a tabela de controle de viaturas.
    """

    def __init__(self):

        # Raiz do projeto
        self.root = Path(__file__).resolve().parent.parent.parent

        # Caminhos
        self.bronze_path = self.root / "data" / "01_bronze" / "active"

        self.silver_path = self.root / "data" / "02_silver"

        # Garante que a pasta exista
        self.silver_path.mkdir(parents=True, exist_ok=True)

        # Mapeamento das colunas
        self.column_map = {
            "Nº chamada": "ID",
            "Recursos empenhados": "Recurso",
            "Data/hora de criação": "Saída",
            "Data/hora da situação atual": "Chegada",
            "Local do fato": "Endereço"
        }

    def process_vehicle_table(self) -> Optional[pd.DataFrame]:


        # 1. Procurar arquivos CSV
        files = list(self.bronze_path.glob("*.csv"))

        print(self.bronze_path)

        print(files)

        if not files:
            logging.warning("Nenhum arquivo CSV encontrado.")
            return None

        # 2. Pegar arquivo mais recente
        latest_file = max(files, key=lambda f: f.stat().st_mtime)

        print(latest_file)

        logging.info(f"Processando: {latest_file.name}")

        try:

            # 3. Ler CSV
            df = pd.read_csv(
                latest_file,
                sep=';',
                encoding='latin1',
                on_bad_lines='skip'
            )


            print(df.head())

            # 4. Selecionar colunas existentes
            existing_cols = [
                col for col in self.column_map.keys()
                if col in df.columns
            ]

            print(existing_cols)

            # 5. Criar novo DataFrame
            df_vehicle = df[existing_cols].rename(columns=self.column_map)

            # Converter colunas de data para datetime real
            for col in ["Saída", "Chegada"]:

                if col in df_vehicle.columns:

                    df_vehicle[col] = pd.to_datetime(
                        df_vehicle[col],
                        dayfirst=True,
                        errors="coerce"
        )
                    
            limite_data = datetime.now() - timedelta(days=MAX_ACTIVE_DAYS)
            df_vehicle = df_vehicle[
                df_vehicle["Saída"] >= limite_data
]

            # 6. Criar colunas vazias
            df_vehicle["Km Saída"] = ""
            df_vehicle["Km Chegada"] = ""
            df_vehicle["Motorista"] = ""

            # Organizar por Recurso e depois por Saída
            df_vehicle = df_vehicle.sort_values(
                by=["Recurso", "Saída"],
                ascending=[True, True]
)
            

            # Voltar datas para formato brasileiro
            for col in ["Saída", "Chegada"]:

                if col in df_vehicle.columns:

                    df_vehicle[col] = df_vehicle[col].dt.strftime(
                        "%d/%m/%Y %H:%M:%S"
        )

            # 7. Organizar ordem das colunas
            final_columns = [
                "ID",
                "Recurso",
                "Saída",
                "Chegada",
                "Km Saída",
                "Km Chegada",
                "Endereço",
                "Motorista"
            ]

            df_vehicle = df_vehicle[final_columns]
            print(df_vehicle.head())

            # 8. Salvar CSV
            output_path = self.silver_path / "vehicle_calls.csv"

            df_vehicle.to_csv(
                output_path,
                index=False,
                encoding='utf-8-sig'
            )
            print(output_path)

            logging.info(f"Tabela salva em: {output_path}")

            return df_vehicle

        except Exception as e:

            print(e)

            logging.error(f"Erro ao processar tabela: {e}")

            return None


# Teste isolado
if __name__ == "__main__":

    processor = VehicleDataProcessor()

    result = processor.process_vehicle_table()

    if result is not None:

        print("\n--- Prévia da Tabela ---")

        print(result.head())