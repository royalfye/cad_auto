import pandas as pd
import os
from pathlib import Path

class DataProcessor:
    """
    Class responsible for the Data Medallion Structure (Bronze -> Silver -> Gold).
    """
    def __init__(self):
        # Path definitions using pathlib for Windows compatibility
        self.base_path = Path("data")
        self.bronze_path = self.base_path / "01_bronze"
        self.silver_path = self.base_path / "02_silver"
        self.gold_path = self.base_path / "03_gold"

    def consolidate_historical_data(self):
        """
        Scans all subfolders in Bronze, merges all CSVs, and saves a master silver file.
        """
        dataframes_list = []
        
        # Recursively find all CSV files
        all_files = list(self.bronze_path.rglob("*.csv"))
        
        if not all_files:
            raise FileNotFoundError("No CSV files found in the 01_bronze directory.")

        for file_path in all_files:
            try:
                # Reading with specific encoding for Brazilian legacy systems
                df = pd.read_csv(
                    file_path, 
                    encoding='latin1', 
                    sep=';', 
                    on_bad_lines='skip'
                )
                
                # Metadata: track which file the data came from
                df['source_file'] = file_path.name
                dataframes_list.append(df)
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")

        # Concatenate all data into a single DataFrame
        master_df = pd.concat(dataframes_list, ignore_index=True)
        
        # Data Cleaning
        master_df.columns = [col.strip() for col in master_df.columns]
        master_df = master_df.drop_duplicates()

        # Save as Master Silver file
        output_file = self.silver_path / "master_historic_silver.csv"
        master_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        return master_df

    def process_bronze_to_silver(self, file_name: str):
        """
        Processes a single raw CSV file from Bronze to Silver layer.
        Used for incremental updates.
        """
        raw_file_path = self.bronze_path / file_name
        
        if not raw_file_path.exists():
            raise FileNotFoundError(f"File {file_name} not found in Bronze layer.")

        # Read individual file
        df = pd.read_csv(
            raw_file_path, 
            encoding='latin1', 
            sep=';', 
            on_bad_lines='skip'
        )

        # Basic cleaning
        df.columns = [col.strip() for col in df.columns]
        df_clean = df.drop_duplicates()

        # Save processed file
        output_name = file_name.replace(".csv", "_silver.csv")
        output_path = self.silver_path / output_name
        df_clean.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        return df_clean