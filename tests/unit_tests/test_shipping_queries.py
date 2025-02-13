"""Test shipping query functions."""

import pytest
from react_agent.tools.queries.shipping import (
    get_shipping_estimate,
    get_shipping_methods,
    get_fastest_routes
)

@pytest.mark.asyncio
async def test_get_shipping_estimate(config):
    """Test shipping estimate query."""
    # First get a warehouse location for Titanium dioxide
    from react_agent.tools.queries.catalog import search_by_criteria
    from react_agent.tools.queries.inventory import get_chemical_inventory

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
    origin = inventory[0]['WarehouseLocation']

    # Test shipping estimate
    results = await get_shipping_estimate(
        origin=origin,
        destination="CA",
        method="Ground",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'OriginLocation' in results[0]
        assert 'BaseRate' in results[0]
        assert 'EstimatedDays' in results[0]
        assert results[0]['OriginLocation'] == origin

@pytest.mark.asyncio
async def test_get_shipping_methods(config):
    """Test shipping methods query."""
    # Get warehouse location
    from react_agent.tools.queries.catalog import search_by_criteria
    from react_agent.tools.queries.inventory import get_chemical_inventory

    chemical = await search_by_criteria(
        chemical_name="Titanium dioxide",
        config=config
    )
    inventory = await get_chemical_inventory(
        chemical_id=chemical[0]['ChemicalId'],
        config=config
    )
    origin = inventory[0]['WarehouseLocation']

    results = await get_shipping_methods(
        origin=origin,
        destination="CA",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'ShippingMethod' in results[0]
        assert 'BaseRate' in results[0]
        assert 'EstimatedDays' in results[0]
        # Only check OriginLocation if we provided an origin
        if origin:
            assert 'OriginLocation' in results[0]
            assert results[0]['OriginLocation'] == origin

@pytest.mark.asyncio
async def test_get_fastest_routes(config):
    """Test fastest routes query."""
    results = await get_fastest_routes(
        destination="CA",
        max_days=3,
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'EstimatedDays' in results[0]
        assert results[0]['EstimatedDays'] <= 3
        assert 'OriginLocation' in results[0], "OriginLocation should be included in response"