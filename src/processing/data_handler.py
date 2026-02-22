import pandas as pd
import logging
import time
from pathlib import Path
from typing import List, Optional

# --- GLOBAL LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DataProcessor:
    """
    Handles the transformation of emergency call data through the Medallion Architecture.
    
    This class orchestrates the cleansing of raw CAD exports (Bronze) into 
    standardized, deduplicated, and technically named datasets (Silver).
    """

    # Constants for maintenance and consistency
    ENCODING_LEGACY: str = 'latin1'
    ENCODING_OUTPUT: str = 'utf-8-sig'
    CSV_SEPARATOR: str = ';'

    def __init__(self) -> None:
        """Initializes paths and technical metadata for the pipeline."""
        self.project_root: Path = Path(__file__).resolve().parent.parent.parent
        self.bronze_path: Path = self.project_root / "data" / "01_bronze"
        self.silver_path: Path = self.project_root / "data" / "02_silver"
        
        # Position-based mapping: Resilient strategy for legacy systems
        self.target_columns: List[str] = [
            "call_id", "reds_number", "created_at", "address", 
            "latitude", "longitude", "nature", "responsible_unit",
            "deployed_resources", "alert_level", "highlight", 
            "involves_authority", "classification_type", "status", 
            "updated_at", "associated_event"
        ]

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Internal helper to create missing folders in the data lake."""
        self.silver_path.mkdir(parents=True, exist_ok=True)

    def _transform_to_silver(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies business rules for the Silver layer:
        1. Drops irrelevant columns.
        2. Standardizes IDs to integer and Timestamps to ISO-8601.
        """
        # 1. Dropping useless columns
        columns_to_drop = [
            "latitude", "longitude", "alert_level", "highlight", 
            "involves_authority", "associated_event"
        ]
        df = df.drop(columns=columns_to_drop, errors='ignore')

        # 2. call_id: Ensuring pure integer
        df['call_id'] = pd.to_numeric(df['call_id'], errors='coerce').fillna(0).astype(int)

        # 3. Timestamps: Standardizing to YYYY-MM-DD HH:MM:SS
        date_columns = ["created_at", "updated_at"]
        for col in date_columns:
            if col in df.columns:
                # dayfirst=True is critical for Brazilian CSV formats
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

        return df

    def _deduplicate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans IDs and removes duplicates based on unique call_id."""
        if 'call_id' in df.columns:
            # Sanitize call_id (remove any non-digit character)
            df['call_id'] = df['call_id'].astype(str).str.replace(r'\D', '', regex=True)
            return df.drop_duplicates(subset=['call_id'], keep='first')
        return df.drop_duplicates()

    def _read_and_standardize_csv(self, path: Path) -> Optional[pd.DataFrame]:
        """Reads a legacy CSV and forces the technical header schema by position."""
        try:
            df = pd.read_csv(
                path, 
                encoding=self.ENCODING_LEGACY, 
                sep=self.CSV_SEPARATOR, 
                on_bad_lines='skip'
            )
            
            # Position-based renaming (The 'Blind' Strategy)
            if len(df.columns) >= len(self.target_columns):
                df.columns = self.target_columns + list(df.columns[len(self.target_columns):])
            
            df['source_file'] = path.name
            return df
        except Exception as e:
            logging.error(f"Standardization failed for {path.name}: {e}")
            return None

    def consolidate_historical_data(self) -> pd.DataFrame:
        """
        Gathers all bronze files, transforms them according to Silver rules,
        and saves a unified Master Silver file.

        Returns:
            pd.DataFrame: The consolidated, cleaned, and typed historical dataset.
        """
        dataframes_list: List[pd.DataFrame] = []
        all_files = list(self.bronze_path.rglob("*.csv"))
        
        if not all_files:
            logging.warning("No CSV files found in 01_bronze directory.")
            return pd.DataFrame()

        for file_path in all_files:
            df = self._read_and_standardize_csv(file_path)
            if df is not None:
                dataframes_list.append(df)

        if not dataframes_list:
            return pd.DataFrame()

        # Concatenation
        master_df = pd.concat(dataframes_list, ignore_index=True)

        # Apply Silver Layer Rules
        master_df = self._deduplicate_data(master_df)
        master_df = self._transform_to_silver(master_df)

        # Persistent storage
        output_file = self.silver_path / "master_historic_silver.csv"
        master_df.to_csv(output_file, index=False, encoding=self.ENCODING_OUTPUT)
        
        logging.info(f"Master Silver updated: {len(master_df)} records saved to {output_file.name}")
        return master_df

    def process_bronze_to_silver(self, file_name: str) -> pd.DataFrame:
        """
        Incremental processing: Takes a single raw file and applies Silver rules.
        """
        raw_file_path = self.bronze_path / file_name
        
        if not raw_file_path.exists():
            logging.error(f"File {file_name} not found in Bronze.")
            return pd.DataFrame()

        df = self._read_and_standardize_csv(raw_file_path)
        if df is not None:
            df = self._deduplicate_data(df)
            df = self._transform_to_silver(df)
            
            output_name = file_name.replace(".csv", "_silver.csv")
            df.to_csv(self.silver_path / output_name, index=False, encoding=self.ENCODING_OUTPUT)
            return df
            
        return pd.DataFrame()