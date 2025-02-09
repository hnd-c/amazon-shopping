"""Tools for querying the chemical catalog database.

This module provides tools for reading and querying chemical catalog data from Supabase.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from typing_extensions import Annotated
from datetime import datetime
import logging

from langchain_core.tools import InjectedToolArg
from langchain_core.runnables import RunnableConfig

from react_agent.configuration import Configuration
from react_agent.database import SupabaseDB

logger = logging.getLogger(__name__)


async def search_chemicals(
    search_term: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Search for chemicals by name, product name, or brand name.

    Args:
        search_term: Text to search for in chemical names and products
        config: Configuration injected by the runtime

    Returns:
        List of matching chemical entries
    """
    logger.info("Received search request with config: %s", config)
    configuration = Configuration.from_runnable_config(config)
    logger.info("Created configuration with URL: %s", configuration.supabase_url[:8])
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_chemicals(search_term=search_term)


async def find_by_cas(
    cas_number: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find chemicals by CAS number.

    Args:
        cas_number: The CAS registry number to search for
        config: Configuration injected by the runtime

    Returns:
        List of matching chemical entries
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_chemicals(filters={"CasNumber": cas_number})


async def find_by_company(
    company_name: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find chemicals by manufacturing company.

    Args:
        company_name: Name of the company to search for
        config: Configuration injected by the runtime

    Returns:
        List of matching chemical entries
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_chemicals(filters={"CompanyName": company_name})


async def find_by_category(
    category: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find chemicals by primary category.

    Args:
        category: The primary category to search for
        config: Configuration injected by the runtime

    Returns:
        List of matching chemical entries
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_chemicals(filters={"PrimaryCategory": category})


async def custom_query(
    filters: Dict[str, Any],
    columns: Optional[List[str]] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Execute a custom query with specific filters and columns.

    Args:
        filters: Dictionary of column-value pairs to filter by
        columns: Optional list of columns to return
        config: Configuration injected by the runtime

    Returns:
        List of matching chemical entries
    """
    logger.info(f"Custom query called with filters: {filters}, columns: {columns}")

    # Ensure config is not None and has configurable
    if not config or "configurable" not in config:
        raise ValueError("Configuration is required")

    configuration = Configuration.from_runnable_config(config)

    # Validate configuration
    if not configuration.supabase_url or not configuration.supabase_key:
        raise ValueError("Supabase credentials are missing")

    logger.info(f"Using Supabase URL: {configuration.supabase_url[:8]}...")

    try:
        db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
        results = await db.query_chemicals(
            filters=filters if filters else {},
            columns=columns
        )
        logger.info(f"Query returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Error in custom_query: {str(e)}")
        raise


async def search_by_chemical_name(
    chemical_name: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Search for products containing a specific chemical.

    Args:
        chemical_name: Name of the chemical to search for
        config: Configuration injected by the runtime
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_chemicals(
        filters={"ChemicalName": chemical_name}
    )


async def search_by_company(
    company_name: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find all products from a specific company.

    Args:
        company_name: Name of the company to search for
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_chemicals(
        filters={"CompanyName": company_name}
    )


async def search_by_category(
    category: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find products in a specific category.

    Args:
        category: Primary category to search for
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_chemicals(
        filters={"PrimaryCategory": category}
    )


async def search_by_brand(
    brand_name: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find products from a specific brand.

    Args:
        brand_name: Brand name to search for
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_chemicals(
        filters={"BrandName": brand_name}
    )


async def search_by_cas(
    cas_number: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find products containing a chemical with specific CAS number.

    Args:
        cas_number: CAS registry number to search for
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_chemicals(
        filters={"CasNumber": cas_number}
    )


async def search_products_by_date_range(
    start_date: str,
    end_date: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find products reported within a date range.

    Args:
        start_date: Start date in format YYYY-MM-DD
        end_date: End date in format YYYY-MM-DD
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_chemicals(
        filters={
            "InitialDateReported": {
                "gte": start_date,
                "lte": end_date
            }
        }
    )


async def find_by_subcategory(
    subcategory: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find products in a specific subcategory."""
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_products_by_subcategory(subcategory)


async def find_discontinued_products(
    before_date: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find discontinued products, optionally before a specific date."""
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_discontinued_products(before_date)


async def get_products_by_date(
    start_date: str,
    end_date: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find products reported between specific dates."""
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_products_by_date_range(start_date, end_date)


async def get_statistics(
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Get statistical information about products in the database."""
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_product_statistics()


async def search_multi_criteria(
    company: Optional[str] = None,
    category: Optional[str] = None,
    chemical: Optional[str] = None,
    brand: Optional[str] = None,
    date_after: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Search products with multiple criteria."""
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.search_multi_criteria(
        company=company,
        category=category,
        chemical=chemical,
        brand=brand,
        date_after=date_after
    )


TOOLS: List[Callable[..., Any]] = [
    search_chemicals,
    find_by_cas,
    find_by_company,
    find_by_category,
    custom_query,
    search_by_chemical_name,
    search_by_company,
    search_by_category,
    search_by_brand,
    search_by_cas,
    search_products_by_date_range,
    find_by_subcategory,
    find_discontinued_products,
    get_products_by_date,
    get_statistics,
    search_multi_criteria
]

def search_chemicals(db: SupabaseDB, query: str, limit: int = 10) -> List[Dict[Any, Any]]:
    """
    Search for chemicals by name, product name, brand name, or CAS number.
    """
    try:
        # Build query to search across multiple fields
        result = db.client.table('ChemicalCatalog').select('*').or_(
            f"ProductName.ilike.%{query}%,"
            f"BrandName.ilike.%{query}%,"
            f"ChemicalName.ilike.%{query}%,"
            f"CasNumber.ilike.%{query}%,"
            f"CompanyName.ilike.%{query}%"
        ).limit(limit).execute()

        logger.info(f"Found {len(result.data)} results for query: {query}")
        return result.data
    except Exception as e:
        logger.error(f"Error searching chemicals: {str(e)}")
        return []

def get_chemical_by_cas(db: SupabaseDB, cas_number: str, limit: int = 10) -> List[Dict[Any, Any]]:
    """
    Find chemicals by CAS number.
    """
    try:
        result = db.client.table('ChemicalCatalog').select('*').eq('CasNumber', cas_number).limit(limit).execute()
        logger.info(f"Found {len(result.data)} results for CAS number: {cas_number}")
        return result.data
    except Exception as e:
        logger.error(f"Error getting chemical by CAS: {str(e)}")
        return []

def get_chemicals_by_company(db: SupabaseDB, company_name: str, limit: int = 10) -> List[Dict[Any, Any]]:
    """
    Find chemicals from a specific company.
    """
    try:
        result = db.client.table('ChemicalCatalog').select('*').ilike('CompanyName', f'%{company_name}%').limit(limit).execute()
        logger.info(f"Found {len(result.data)} results for company: {company_name}")
        return result.data
    except Exception as e:
        logger.error(f"Error getting chemicals by company: {str(e)}")
        return []

def get_chemicals_by_category(db: SupabaseDB, category: str, limit: int = 10) -> List[Dict[Any, Any]]:
    """
    Find chemicals by category.
    """
    try:
        result = db.client.table('ChemicalCatalog').select('*').or_(
            f"PrimaryCategory.ilike.%{category}%,"
            f"SubCategory.ilike.%{category}%"
        ).limit(limit).execute()
        logger.info(f"Found {len(result.data)} results for category: {category}")
        return result.data
    except Exception as e:
        logger.error(f"Error getting chemicals by category: {str(e)}")
        return []
