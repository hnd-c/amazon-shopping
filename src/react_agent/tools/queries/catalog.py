"""Chemical catalog query tools."""

from typing import Any, Dict, List, Optional
from typing_extensions import Annotated
from langchain_core.tools import InjectedToolArg
from langchain_core.runnables import RunnableConfig
import logging

from react_agent.configuration import Configuration
from react_agent.tools.database import SupabaseDB

logger = logging.getLogger(__name__)

async def search_chemicals(
    search_term: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Search for chemicals by name, product name, or brand name.

    Args:
        search_term: Text to search for in chemical names and products
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_chemicals(search_term=search_term)

async def search_by_criteria(
    *,
    cas_number: Optional[str] = None,
    company_name: Optional[str] = None,
    category: Optional[str] = None,
    brand_name: Optional[str] = None,
    chemical_name: Optional[str] = None,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Search chemicals by various criteria.

    Args:
        cas_number: CAS registry number
        company_name: Manufacturing company name
        category: Primary category
        brand_name: Brand name
        chemical_name: Chemical name
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)

    filters = {}
    if cas_number:
        filters['CasNumber'] = cas_number
    if company_name:
        filters['CompanyName'] = company_name
    if category:
        filters['PrimaryCategory'] = category
    if brand_name:
        filters['BrandName'] = brand_name
    if chemical_name:
        filters['ChemicalName'] = chemical_name

    return await db.query_chemicals(filters=filters)

async def search_by_date_range(
    start_date: str,
    end_date: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Search for products within a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)

    filters = {
        'InitialDateReported': {
            'gte': start_date,
            'lte': end_date
        }
    }
    return await db.query_chemicals(filters=filters)

async def get_discontinued_products(
    before_date: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get discontinued products, optionally before a specific date.

    Args:
        before_date: Optional date in YYYY-MM-DD format
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_discontinued_products(before_date)

async def get_products_by_subcategory(
    subcategory: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get products in a specific subcategory.

    Args:
        subcategory: Product subcategory
    """
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_products_by_subcategory(subcategory)

async def get_statistics(
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Get statistical information about products in the database."""
    configuration = Configuration.from_runnable_config(config)
    db = SupabaseDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_product_statistics()

# List of available query tools
CATALOG_TOOLS = [
    search_chemicals,
    search_by_criteria,
    search_by_date_range,
    get_discontinued_products,
    get_products_by_subcategory,
    get_statistics
]
