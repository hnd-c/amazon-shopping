"""Test pricing query functions."""

import pytest
from react_agent.tools.queries.pricing import (
    get_chemical_price,
    get_price_history,
    search_prices_by_currency
)

@pytest.mark.asyncio
async def test_get_chemical_price(config):
    """Test chemical price query."""
    # First get a valid chemical ID for Titanium dioxide
    from react_agent.tools.queries.catalog import search_by_criteria
    results = await search_by_criteria(
        chemical_name="Titanium dioxide",
        config=config
    )
    assert len(results) > 0, "Should find Titanium dioxide to get its ID"
    chemical_id = results[0]['ChemicalId']

    # Test price query
    prices = await get_chemical_price(
        chemical_id=chemical_id,
        config=config
    )
    assert isinstance(prices, list)
    if prices:
        assert 'ChemicalId' in prices[0]
        assert 'Price' in prices[0]
        assert 'Currency' in prices[0]
        assert prices[0]['ChemicalId'] == chemical_id

@pytest.mark.asyncio
async def test_get_price_history(config):
    """Test price history query."""
    # Get chemical ID for Titanium dioxide
    from react_agent.tools.queries.catalog import search_by_criteria
    results = await search_by_criteria(
        chemical_name="Titanium dioxide",
        config=config
    )
    assert len(results) > 0, "Should find Titanium dioxide to get its ID"
    chemical_id = results[0]['ChemicalId']

    # Test history query
    history = await get_price_history(
        chemical_id=chemical_id,
        start_date="2020-01-01",
        end_date="2024-12-31",
        config=config
    )
    assert isinstance(history, list)
    if history:
        assert 'ChemicalId' in history[0]
        assert 'Price' in history[0]
        assert 'EffectiveDate' in history[0]
        assert history[0]['ChemicalId'] == chemical_id

@pytest.mark.asyncio
async def test_search_prices_by_currency(config):
    """Test currency search."""
    results = await search_prices_by_currency(
        currency="USD",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'Currency' in results[0]
        assert results[0]['Currency'] == "USD"