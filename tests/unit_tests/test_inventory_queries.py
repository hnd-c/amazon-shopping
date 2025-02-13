"""Test inventory query functions."""

import pytest
from react_agent.tools.queries.inventory import (
    get_chemical_inventory,
    get_warehouse_inventory,
    get_low_stock_items
)

@pytest.mark.asyncio
async def test_get_chemical_inventory(config):
    """Test chemical inventory query."""
    # First get a valid chemical ID for Titanium dioxide
    from react_agent.tools.queries.catalog import search_by_criteria
    results = await search_by_criteria(
        chemical_name="Titanium dioxide",
        config=config
    )
    assert len(results) > 0, "Should find Titanium dioxide to get its ID"
    chemical_id = results[0]['ChemicalId']

    # Test inventory query
    inventory = await get_chemical_inventory(
        chemical_id=chemical_id,
        config=config
    )
    assert isinstance(inventory, list)
    if inventory:
        assert 'ChemicalId' in inventory[0]
        assert 'AvailableQuantity' in inventory[0]
        assert 'Unit' in inventory[0]
        assert inventory[0]['ChemicalId'] == chemical_id

@pytest.mark.asyncio
async def test_get_warehouse_inventory(config):
    """Test warehouse inventory query."""
    # Get a warehouse that has Titanium dioxide
    from react_agent.tools.queries.catalog import search_by_criteria
    chemical = await search_by_criteria(
        chemical_name="Titanium dioxide",
        config=config
    )
    assert len(chemical) > 0, "Should find Titanium dioxide"

    inventory = await get_chemical_inventory(
        chemical_id=chemical[0]['ChemicalId'],
        config=config
    )
    assert len(inventory) > 0, "Should find inventory for Titanium dioxide"
    warehouse = inventory[0]['WarehouseLocation']

    # Test warehouse query
    results = await get_warehouse_inventory(
        warehouse=warehouse,
        min_quantity=0,  # Include all quantities
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'WarehouseLocation' in results[0]
        assert 'AvailableQuantity' in results[0]
        assert results[0]['WarehouseLocation'] == warehouse

@pytest.mark.asyncio
async def test_get_low_stock_items(config):
    """Test low stock query."""
    results = await get_low_stock_items(
        threshold=50,
        warehouse="Warehouse A",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'AvailableQuantity' in results[0]
        assert results[0]['AvailableQuantity'] <= 50