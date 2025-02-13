"""Chemical inventory query tools."""

from typing import Any, Dict, List, Optional
from typing_extensions import Annotated
from langchain_core.tools import InjectedToolArg
from langchain_core.runnables import RunnableConfig
import logging

from react_agent.configuration import Configuration
from react_agent.tools.database.inventory import ChemicalInventoryDB

logger = logging.getLogger(__name__)

async def get_chemical_inventory(
    chemical_id: int,
    warehouse: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get inventory levels for a chemical.

    Args:
        chemical_id: ID of the chemical
        warehouse: Optional warehouse location
    """
    configuration = Configuration.from_runnable_config(config)
    db = ChemicalInventoryDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_chemical_inventory(chemical_id, warehouse)

async def get_warehouse_inventory(
    warehouse: str,
    min_quantity: Optional[float] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get inventory in a specific warehouse.

    Args:
        warehouse: Warehouse location
        min_quantity: Optional minimum quantity filter
    """
    configuration = Configuration.from_runnable_config(config)
    db = ChemicalInventoryDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_warehouse_inventory(warehouse, min_quantity)

async def get_low_stock_items(
    threshold: float,
    warehouse: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get items with stock below threshold.

    Args:
        threshold: Stock threshold
        warehouse: Optional warehouse location
    """
    configuration = Configuration.from_runnable_config(config)
    db = ChemicalInventoryDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_low_stock_items(threshold, warehouse)

# List of available inventory tools
INVENTORY_TOOLS = [
    get_chemical_inventory,
    get_warehouse_inventory,
    get_low_stock_items
]