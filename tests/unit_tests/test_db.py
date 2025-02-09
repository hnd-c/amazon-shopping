"""Test script to verify database connectivity and queries."""
import os
import sys
import asyncio
from dotenv import load_dotenv
import logging

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.react_agent.database import SupabaseDB

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_queries():
    """Run test queries against the database."""
    # Load environment variables
    load_dotenv()

    # Get credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        logger.error("Missing Supabase credentials in .env file")
        return

    logger.info("Initializing database connection...")
    db = SupabaseDB(url, key)

    # Test simple SQL query first
    logger.info("\nTest 0: Direct SQL query")
    try:
        result = db.client.table('ChemicalCatalog').select('count').execute()
        logger.info(f"Total records in database: {len(result.data)}")
        logger.info(f"SQL Query: {result.query}")
    except Exception as e:
        logger.error(f"Direct query failed: {str(e)}")

    # Test 1: Basic search
    logger.info("\nTest 1: Basic search for titanium dioxide")
    try:
        query = db.client.table('ChemicalCatalog').select(
            'ProductName,CompanyName,BrandName,ChemicalName,CasNumber,PrimaryCategory'
        ).eq('CasNumber', '13463-67-7')
        result = query.execute()
        logger.info(f"SQL Query: {result.query}")
        logger.info(f"Found {len(result.data)} products")
        if result.data:
            logger.info("Sample products:")
            for product in result.data[:3]:
                logger.info(f"- {product['ProductName']} by {product['CompanyName']}")
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")

    # Test 2: Search by CAS number
    logger.info("\nTest 2: Search by CAS number")
    results = await db.query_chemicals(filters={"CasNumber": "13463-67-7"})
    logger.info(f"Found {len(results)} products with CAS number 13463-67-7")
    if results:
        logger.info("Sample products:")
        for product in results[:3]:
            logger.info(f"- {product['ProductName']} ({product['ChemicalName']})")

    # Test 3: Search by subcategory
    logger.info("\nTest 3: Search lipstick products")
    results = await db.get_products_by_subcategory("Lipstick")
    logger.info(f"Found {len(results)} lipstick products")
    if results:
        logger.info("Sample products:")
        for product in results[:3]:
            logger.info(f"- {product['ProductName']} by {product['CompanyName']}")

    # Test 4: Get discontinued products
    logger.info("\nTest 4: Get discontinued products")
    results = await db.get_discontinued_products("2012-01-01")
    logger.info(f"Found {len(results)} discontinued products before 2012")
    if results:
        logger.info("Sample discontinued products:")
        for product in results[:3]:
            logger.info(f"- {product['ProductName']} (Discontinued: {product['DiscontinuedDate']})")

    # Test 5: Date range search
    logger.info("\nTest 5: Products reported in 2009")
    results = await db.get_products_by_date_range("2009-01-01", "2009-12-31")
    logger.info(f"Found {len(results)} products reported in 2009")
    if results:
        logger.info("Sample products:")
        for product in results[:3]:
            logger.info(f"- {product['ProductName']} (Reported: {product['InitialDateReported']})")

    # Test 6: Get statistics
    logger.info("\nTest 6: Get database statistics")
    stats = await db.get_product_statistics()
    if stats:
        logger.info("Database statistics:")
        if 'categories' in stats:
            logger.info("Top categories:")
            for cat in list(stats['categories'])[:3]:
                logger.info(f"- {cat['PrimaryCategory']}: {cat['count']} products")
        if 'companies' in stats:
            logger.info("Top companies:")
            for comp in list(stats['companies'])[:3]:
                logger.info(f"- {comp['CompanyName']}: {comp['count']} products")

    # Test 7: Multi-criteria search
    logger.info("\nTest 7: Multi-criteria search")
    results = await db.search_multi_criteria(
        company="AVON",
        category="Makeup",
        chemical="Titanium dioxide",
        date_after="2009-01-01"
    )
    logger.info(f"Found {len(results)} AVON makeup products with titanium dioxide after 2009")
    if results:
        logger.info("Sample products:")
        for product in results[:3]:
            logger.info(f"- {product['ProductName']}")

if __name__ == "__main__":
    asyncio.run(test_database_queries())