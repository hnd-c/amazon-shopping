"""Script to load CSV data into Supabase."""
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import logging
from src.react_agent.database import SupabaseDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data():
    """Load data from CSV to Supabase."""
    # Load environment variables
    load_dotenv()

    # Get credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        logger.error("Missing Supabase credentials")
        return

    # Load CSV data
    logger.info("Loading CSV data...")
    df = pd.read_csv('output_with_uuid.csv')
    logger.info(f"Loaded {len(df)} rows from CSV")

    # Handle dates - convert to proper format or None
    date_columns = ['InitialDateReported', 'MostRecentDateReported', 'DiscontinuedDate',
                   'ChemicalCreatedAt', 'ChemicalUpdatedAt', 'ChemicalDateRemoved']
    for col in date_columns:
        if col in df.columns:
            # Convert to datetime, coerce errors to NaT
            df[col] = pd.to_datetime(df[col], errors='coerce')
            # Convert to string format where valid, None where NaT
            df[col] = df[col].map(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None)

    # Replace NaN values with None
    df = df.replace({np.nan: None})

    # Convert numeric columns to Int64 (nullable integer type)
    numeric_columns = ['CDPHId', 'CompanyId', 'PrimaryCategoryId', 'SubCategoryId',
                      'CasId', 'ChemicalId', 'ChemicalCount']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.array(df[col], dtype=pd.Int64Dtype())

    # Convert DataFrame to records
    records = df.to_dict('records')

    # Connect to Supabase
    logger.info("Connecting to Supabase...")
    db = SupabaseDB(url, key)

    # Insert in batches
    BATCH_SIZE = 100
    total = 0

    logger.info("Inserting data...")
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        try:
            result = db.client.table('ChemicalCatalog').insert(batch).execute()
            total += len(batch)
            logger.info(f"Inserted {total}/{len(records)} records")
        except Exception as e:
            logger.error(f"Error inserting batch {i//BATCH_SIZE}: {str(e)}")
            if batch:
                logger.error(f"Sample record: {batch[0]}")
            continue

if __name__ == "__main__":
    load_data()