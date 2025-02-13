"""Chemical pricing query tools."""

from typing import Any, Dict, List, Optional
from typing_extensions import Annotated
from langchain_core.tools import InjectedToolArg
from langchain_core.runnables import RunnableConfig
import logging

from react_agent.configuration import Configuration
from react_agent.tools.database.pricing import ChemicalPricingDB

logger = logging.getLogger(__name__)

async def get_chemical_price(
    chemical_id: int,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get current price for a chemical.

    Args:
        chemical_id: ID of the chemical
    """
    configuration = Configuration.from_runnable_config(config)
    db = ChemicalPricingDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_latest_prices(chemical_id)

async def get_price_history(
    chemical_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get price history for a chemical.

    Args:
        chemical_id: ID of the chemical
        start_date: Optional start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
    """
    configuration = Configuration.from_runnable_config(config)
    db = ChemicalPricingDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_price_history(chemical_id, start_date, end_date)

async def search_prices_by_currency(
    currency: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Search prices by currency.

    Args:
        currency: Currency code (e.g., USD, EUR)
    """
    configuration = Configuration.from_runnable_config(config)
    db = ChemicalPricingDB(configuration.supabase_url, configuration.supabase_key)
    return await db.query_prices(currency=currency)

# List of available pricing tools
PRICING_TOOLS = [
    get_chemical_price,
    get_price_history,
    search_prices_by_currency
]