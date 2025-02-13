"""Tools package."""

from react_agent.tools.queries.catalog import CATALOG_TOOLS
from react_agent.tools.queries.pricing import PRICING_TOOLS
from react_agent.tools.queries.compliance import COMPLIANCE_TOOLS
from react_agent.tools.queries.shipping import SHIPPING_TOOLS
from react_agent.tools.queries.inventory import INVENTORY_TOOLS

# Combine all tools
TOOLS = (
    CATALOG_TOOLS +
    PRICING_TOOLS +
    COMPLIANCE_TOOLS +
    SHIPPING_TOOLS +
    INVENTORY_TOOLS
)

__all__ = ['TOOLS']