"""Shipping estimates query tools."""

from typing import Any, Dict, List, Optional
from typing_extensions import Annotated
from langchain_core.tools import InjectedToolArg
from langchain_core.runnables import RunnableConfig
import logging

from react_agent.configuration import Configuration
from react_agent.tools.database.shipping import ShippingEstimatesDB

logger = logging.getLogger(__name__)

async def get_shipping_estimate(
    origin: str,
    destination: str,
    method: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get shipping estimates for a route.

    Args:
        origin: Origin location
        destination: Destination state
        method: Optional shipping method
    """
    configuration = Configuration.from_runnable_config(config)
    db = ShippingEstimatesDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_shipping_estimate(origin, destination, method)

async def get_shipping_methods(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get available shipping methods.

    Args:
        origin: Optional origin location filter
        destination: Optional destination state filter
    """
    configuration = Configuration.from_runnable_config(config)
    db = ShippingEstimatesDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_shipping_methods(origin, destination)

async def get_fastest_routes(
    destination: str,
    max_days: Optional[int] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get fastest shipping routes to a destination.

    Args:
        destination: Destination state
        max_days: Optional maximum days for delivery
    """
    configuration = Configuration.from_runnable_config(config)
    db = ShippingEstimatesDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_fastest_routes(destination, max_days)

# List of available shipping tools
SHIPPING_TOOLS = [
    get_shipping_estimate,
    get_shipping_methods,
    get_fastest_routes
]