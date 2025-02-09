import os
import logging
from react_agent.configuration import Configuration
from react_agent.database import SupabaseDB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_configuration():
    """Verify the configuration and database connection."""
    # Print raw environment variables
    logger.info("Raw environment variables:")
    logger.info(f"SUPABASE_URL length: {len(os.environ.get('SUPABASE_URL', ''))}")
    logger.info(f"SUPABASE_ANON_KEY length: {len(os.environ.get('SUPABASE_ANON_KEY', ''))}")

    logger.info("\nCreating configuration...")
    config = Configuration()

    # Print configuration values
    logger.info("\nConfiguration values:")
    logger.info(f"Supabase URL length: {len(config.supabase_url)}")
    logger.info(f"Supabase Key length: {len(config.supabase_key)}")

    # Test actual values match
    logger.info("\nValue comparison:")
    logger.info(f"URLs match: {config.supabase_url == os.environ.get('SUPABASE_URL')}")
    logger.info(f"Keys match: {config.supabase_key == os.environ.get('SUPABASE_ANON_KEY')}")

    logger.info("\nTesting database connection...")
    db = SupabaseDB(config.supabase_url, config.supabase_key)

    # Try a simple query
    logger.info("\nTesting query...")
    try:
        result = db.client.table('ChemicalCatalog').select('*').limit(1).execute()
        logger.info(f"Query successful! Found {len(result.data)} records")
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")

    return config, db

if __name__ == "__main__":
    config, db = verify_configuration()
    logger.info("Configuration verified successfully!")