"""Amazon search tool for the React Agent."""

import asyncio
from typing import Any, Dict, List, Optional, Union
from typing_extensions import Annotated
from langchain_core.tools import InjectedToolArg
from langchain_core.runnables import RunnableConfig
import logging

from .main import AmazonConnection, search_amazon

logger = logging.getLogger(__name__)

# Browser management helper functions
async def get_or_create_browser(config: Dict[str, Any]) -> AmazonConnection:
    """Get existing browser from config or create a new one."""
    browser = config.get("browser")

    if browser is None or not isinstance(browser, AmazonConnection):
        logger.info("Creating new AmazonConnection browser")
        browser = AmazonConnection(
            headless=config.get("headless", True),
            slow_mo=config.get("browser_slow_mo", 50),
            proxy=config.get("browser_proxy", None),
            proxies=config.get("browser_proxies", None)
        )
        await browser.start()
        config["browser"] = browser
        # Set a flag to indicate this browser was created by this function
        config["browser_created_by_tool"] = True

    return browser

async def close_browser_if_created(config: Dict[str, Any]) -> None:
    """Close the browser if it was created by the tool."""
    if config.get("browser_created_by_tool") and config.get("browser"):
        logger.info("Closing AmazonConnection browser created by tool")
        await config["browser"].close()
        config["browser"] = None
        config["browser_created_by_tool"] = False

# Enhanced search function with retry logic
async def search_amazon_products_with_retry(
    query: str,
    *,
    # Price filters
    price_min: Optional[str] = None,
    price_max: Optional[str] = None,
    # Shipping and availability filters
    prime_only: bool = False,
    free_shipping: bool = False,
    max_delivery_days: Optional[int] = None,
    availability: Optional[str] = None,
    # Brand and seller filters
    brand: Optional[str] = None,
    seller: Optional[str] = None,
    # Rating and review filters
    min_rating: Optional[int] = None,
    customer_reviews: Optional[str] = None,
    # Deal filters
    discount_only: bool = False,
    deals: bool = False,
    # Product attribute filters
    condition: Optional[str] = None,
    department: Optional[str] = None,
    category: Optional[str] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
    material: Optional[str] = None,
    features: Optional[str] = None,
    # Sorting and display
    sort_by: Optional[str] = "review-rank",
    max_results: int = 5,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Search for products on Amazon with comprehensive filtering and retry logic."""
    max_retries = 3
    retry_delay = 2  # seconds

    # Build filters dictionary
    filters = {}
    locals_copy = locals().copy()
    for param, value in locals_copy.items():
        if param not in ['query', 'filters', 'max_results', 'config', 'max_retries',
                         'retry_delay', 'locals_copy']:
            if value is not None and not (isinstance(value, bool) and value is False):
                filters[param] = value

    # Process special parameters
    if brand and isinstance(brand, str) and "," in brand:
        filters["brand"] = [b.strip() for b in brand.split(",")]

    if features and isinstance(features, str) and "," in features:
        filters["features"] = [f.strip() for f in features.split(",")]

    for attempt in range(max_retries):
        try:
            # Get or create browser
            browser = await get_or_create_browser(config)

            # Execute search
            logger.info(f"Searching Amazon for: {query} (attempt {attempt+1}/{max_retries})")
            products = await browser.search_products(query)

            if filters:
                logger.info(f"Applying filters: {filters}")
                products = await browser.apply_filters(filters)

            # Format results
            formatted_results = []
            for product in products[:max_results]:
                formatted_product = {
                    "title": product.get("title", "Unknown"),
                    "price": product.get("price", "N/A"),
                    "url": product.get("url", ""),
                    "asin": product.get("asin", ""),
                    "prime_eligible": product.get("prime_eligible", False)
                }

                # Add optional fields if available
                for field in ["rating", "review_count", "availability", "delivery_info"]:
                    if field in product:
                        formatted_product[field] = product[field]

                formatted_results.append(formatted_product)

            logger.info(f"Found {len(formatted_results)} products for query: {query}")
            return formatted_results

        except Exception as e:
            error_type = str(type(e).__name__)
            error_msg = str(e)

            # Handle specific error types
            if "blocked" in error_msg.lower() or "captcha" in error_msg.lower():
                logger.warning(f"Amazon blocking detected: {error_msg}")
                if attempt < max_retries - 1:
                    # Rotate proxy or user agent if available
                    browser = config.get("browser")
                    if browser and hasattr(browser, "rotate_proxy"):
                        logger.info("Rotating proxy and trying again")
                        await browser.rotate_proxy()
                    # Wait before retry with exponential backoff
                    backoff_time = retry_delay * (2 ** attempt)
                    logger.info(f"Waiting {backoff_time}s before retry")
                    await asyncio.sleep(backoff_time)
                    continue
                return [{"error": "Access temporarily blocked by Amazon. Please try again later."}]

            # Network errors
            if any(err in error_msg.lower() for err in ["network", "timeout", "connection"]):
                logger.warning(f"Network error: {error_msg}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return [{"error": f"Network error: {error_msg}. Please check your connection."}]

            # General errors
            logger.error(f"Error searching Amazon ({error_type}): {error_msg}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return [{"error": f"Failed to search Amazon: {error_msg}"}]

    # If we get here, all retries failed
    return [{"error": "Failed to complete search after multiple attempts."}]

# Replace the original search_amazon_products with our enhanced version
async def search_amazon_products(
    query: str,
    *,
    # Price filters
    price_min: Optional[str] = None,
    price_max: Optional[str] = None,
    # Shipping and availability filters
    prime_only: bool = False,
    free_shipping: bool = False,
    max_delivery_days: Optional[int] = None,
    availability: Optional[str] = None,
    # Brand and seller filters
    brand: Optional[str] = None,
    seller: Optional[str] = None,
    # Rating and review filters
    min_rating: Optional[int] = None,
    customer_reviews: Optional[str] = None,
    # Deal filters
    discount_only: bool = False,
    deals: bool = False,
    # Product attribute filters
    condition: Optional[str] = None,
    department: Optional[str] = None,
    category: Optional[str] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
    material: Optional[str] = None,
    features: Optional[str] = None,
    # Sorting and display
    sort_by: Optional[str] = "review-rank",
    max_results: int = 5,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Search for products on Amazon with comprehensive filtering options."""
    try:
        return await search_amazon_products_with_retry(
            query=query,
            price_min=price_min,
            price_max=price_max,
            prime_only=prime_only,
            free_shipping=free_shipping,
            max_delivery_days=max_delivery_days,
            availability=availability,
            brand=brand,
            seller=seller,
            min_rating=min_rating,
            customer_reviews=customer_reviews,
            discount_only=discount_only,
            deals=deals,
            condition=condition,
            department=department,
            category=category,
            color=color,
            size=size,
            material=material,
            features=features,
            sort_by=sort_by,
            max_results=max_results,
            config=config
        )
    finally:
        # Only close the browser if we're not in a chain of Amazon tool calls
        if not config.get("keep_browser_open"):
            await close_browser_if_created(config)

async def find_deals(
    category: str,
    *,
    price_max: Optional[str] = None,
    prime_only: bool = True,
    min_rating: Optional[int] = 4,
    max_results: int = 5,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find current deals and discounts on Amazon in a specific category.

    Args:
        category: Product category (e.g. "electronics", "home", "kitchen")
        price_max: Maximum price (e.g. "99.99")
        prime_only: Only show Prime eligible items
        min_rating: Minimum star rating (1-5)
        max_results: Maximum number of results to return

    Returns:
        List of deal products with price, rating, and discount information
    """
    logger.info(f"Finding deals in category: {category}")
    max_retries = 3
    retry_delay = 2  # seconds

    # Build filters for deals search
    filters = {
        "deals": True,
        "discount_only": True,
        "category": category,
        "prime_only": prime_only,
        "sort_by": "price-asc"
    }

    if price_max:
        filters["price_max"] = price_max
    if min_rating:
        filters["min_rating"] = min_rating

    for attempt in range(max_retries):
        try:
            # Get or create browser
            browser = await get_or_create_browser(config)

            # Execute search
            logger.info(f"Searching Amazon deals for: {category} (attempt {attempt+1}/{max_retries})")
            products = await browser.search_products(category)

            if filters:
                logger.info(f"Applying filters: {filters}")
                products = await browser.apply_filters(filters)

            # Format the results
            formatted_results = []
            for product in products[:max_results]:
                formatted_product = {
                    "title": product.get("title", "Unknown"),
                    "price": product.get("price", "N/A"),
                    "url": product.get("url", ""),
                    "prime_eligible": product.get("prime_eligible", False),
                    "deal_type": "Discount/Deal"
                }

                # Add rating if available
                if "rating" in product:
                    formatted_product["rating"] = product["rating"]

                formatted_results.append(formatted_product)

            logger.info(f"Found {len(formatted_results)} deals in category: {category}")
            return formatted_results

        except Exception as e:
            error_type = str(type(e).__name__)
            error_msg = str(e)

            # Handle specific error types
            if "blocked" in error_msg.lower() or "captcha" in error_msg.lower():
                logger.warning(f"Amazon blocking detected: {error_msg}")
                if attempt < max_retries - 1:
                    # Rotate proxy or user agent if available
                    browser = config.get("browser")
                    if browser and hasattr(browser, "rotate_proxy"):
                        logger.info("Rotating proxy and trying again")
                        await browser.rotate_proxy()
                    # Wait before retry with exponential backoff
                    backoff_time = retry_delay * (2 ** attempt)
                    logger.info(f"Waiting {backoff_time}s before retry")
                    await asyncio.sleep(backoff_time)
                    continue
                return [{"error": "Access temporarily blocked by Amazon. Please try again later."}]

            # Network errors
            if any(err in error_msg.lower() for err in ["network", "timeout", "connection"]):
                logger.warning(f"Network error: {error_msg}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return [{"error": f"Network error: {error_msg}. Please check your connection."}]

            # General errors
            logger.error(f"Error finding deals ({error_type}): {error_msg}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return [{"error": f"Failed to find deals: {error_msg}"}]

    # If we get here, all retries failed
    return [{"error": "Failed to find deals after multiple attempts."}]

async def compare_products(
    product_urls: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Compare multiple Amazon products side by side.

    Args:
        product_urls: Comma-separated list of Amazon product URLs to compare

    Returns:
        Comparison of products with key features, prices, and ratings
    """
    logger.info(f"Comparing products")
    max_retries = 3
    retry_delay = 2  # seconds

    # Split URLs
    urls = [url.strip() for url in product_urls.split(",")]
    if len(urls) < 2:
        return {"error": "Please provide at least two product URLs to compare"}

    if len(urls) > 5:
        urls = urls[:5]  # Limit to 5 products for comparison

    for attempt in range(max_retries):
        try:
            # Get or create browser
            browser = await get_or_create_browser(config)

            products = []
            for url in urls:
                details = await browser.get_product_details(url)
                if details:
                    products.append({
                        "title": details.get("title", "Unknown"),
                        "price": details.get("price", "N/A"),
                        "rating": details.get("rating", "N/A"),
                        "prime_eligible": details.get("prime_eligible", False),
                        "features": details.get("features", [])[:3],  # Top 3 features
                        "url": url
                    })

            # Create comparison result
            comparison = {
                "products": products,
                "comparison_summary": {
                    "price_range": f"{min([p.get('price', '$0') for p in products])} - {max([p.get('price', '$0') for p in products])}",
                    "highest_rated": max(products, key=lambda x: float(x.get("rating", "0").split()[0]) if x.get("rating") else 0).get("title"),
                    "total_compared": len(products)
                }
            }

            return comparison

        except Exception as e:
            error_type = str(type(e).__name__)
            error_msg = str(e)

            # Handle specific error types
            if "blocked" in error_msg.lower() or "captcha" in error_msg.lower():
                logger.warning(f"Amazon blocking detected: {error_msg}")
                if attempt < max_retries - 1:
                    # Rotate proxy or user agent if available
                    if browser and hasattr(browser, "rotate_proxy"):
                        logger.info("Rotating proxy and trying again")
                        await browser.rotate_proxy()
                    # Wait before retry with exponential backoff
                    backoff_time = retry_delay * (2 ** attempt)
                    logger.info(f"Waiting {backoff_time}s before retry")
                    await asyncio.sleep(backoff_time)
                    continue
                return {"error": "Access temporarily blocked by Amazon. Please try again later."}

            # Network errors
            if any(err in error_msg.lower() for err in ["network", "timeout", "connection"]):
                logger.warning(f"Network error: {error_msg}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return {"error": f"Network error: {error_msg}. Please check your connection."}

            # General errors
            logger.error(f"Error comparing products ({error_type}): {error_msg}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return {"error": f"Failed to compare products: {error_msg}"}

    # If we get here, all retries failed
    return {"error": "Failed to compare products after multiple attempts."}

async def find_bestsellers(
    category: str,
    *,
    prime_only: bool = False,
    max_results: int = 5,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find bestselling products in a specific category on Amazon.

    Args:
        category: Product category (e.g. "electronics", "books", "toys")
        prime_only: Only show Prime eligible items
        max_results: Maximum number of results to return

    Returns:
        List of bestselling products in the specified category
    """
    logger.info(f"Finding bestsellers in category: {category}")
    max_retries = 3
    retry_delay = 2  # seconds

    # Build filters for bestseller search
    filters = {
        "category": category,
        "prime_only": prime_only,
        "sort_by": "review-rank",
        "min_rating": 4
    }

    for attempt in range(max_retries):
        try:
            # Get or create browser
            browser = await get_or_create_browser(config)

            # Execute search
            logger.info(f"Searching Amazon bestsellers for: {category} (attempt {attempt+1}/{max_retries})")
            products = await browser.search_products(f"best {category}")

            if filters:
                logger.info(f"Applying filters: {filters}")
                products = await browser.apply_filters(filters)

            # Format the results
            formatted_results = []
            for product in products[:max_results]:
                formatted_product = {
                    "title": product.get("title", "Unknown"),
                    "price": product.get("price", "N/A"),
                    "url": product.get("url", ""),
                    "rating": product.get("rating", "N/A"),
                    "prime_eligible": product.get("prime_eligible", False),
                    "bestseller_rank": f"#{len(formatted_results)+1} in {category}"
                }

                formatted_results.append(formatted_product)

            logger.info(f"Found {len(formatted_results)} bestsellers in category: {category}")
            return formatted_results

        except Exception as e:
            error_type = str(type(e).__name__)
            error_msg = str(e)

            # Handle specific error types
            if "blocked" in error_msg.lower() or "captcha" in error_msg.lower():
                logger.warning(f"Amazon blocking detected: {error_msg}")
                if attempt < max_retries - 1:
                    # Rotate proxy or user agent if available
                    if browser and hasattr(browser, "rotate_proxy"):
                        logger.info("Rotating proxy and trying again")
                        await browser.rotate_proxy()
                    # Wait before retry with exponential backoff
                    backoff_time = retry_delay * (2 ** attempt)
                    logger.info(f"Waiting {backoff_time}s before retry")
                    await asyncio.sleep(backoff_time)
                    continue
                return [{"error": "Access temporarily blocked by Amazon. Please try again later."}]

            # Network errors
            if any(err in error_msg.lower() for err in ["network", "timeout", "connection"]):
                logger.warning(f"Network error: {error_msg}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return [{"error": f"Network error: {error_msg}. Please check your connection."}]

            # General errors
            logger.error(f"Error finding bestsellers ({error_type}): {error_msg}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return [{"error": f"Failed to find bestsellers: {error_msg}"}]

    # If we get here, all retries failed
    return [{"error": "Failed to find bestsellers after multiple attempts."}]

async def get_product_details(
    product_url: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Get detailed information about a specific Amazon product.

    Args:
        product_url: The URL of the Amazon product

    Returns:
        Detailed product information including features, specifications, and reviews
    """
    logger.info(f"Getting details for product: {product_url}")
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            # Get or create browser
            browser = await get_or_create_browser(config)

            logger.info(f"Fetching product details (attempt {attempt+1}/{max_retries})")
            details = await browser.get_product_details(product_url)
            reviews = await browser.get_product_reviews(product_url)

            # Format the response
            result = {
                "title": details.get("title", "Unknown"),
                "price": details.get("price", "N/A"),
                "rating": details.get("rating", "N/A"),
                "prime_eligible": details.get("prime_eligible", False),
                "availability": details.get("availability", "Unknown")
            }

            # Add delivery info if available
            if "delivery_info" in details:
                result["delivery_info"] = details["delivery_info"]

            # Add description if available
            if "description" in details and details["description"]:
                result["description"] = details["description"]

            # Add features if available
            if "features" in details and details["features"]:
                result["features"] = details["features"][:5]  # Limit to top 5 features

            # Add specifications if available
            if "specifications" in details and details["specifications"]:
                result["specifications"] = details["specifications"]

            # Add reviews if available
            if reviews:
                result["reviews"] = []
                for review in reviews[:3]:  # Limit to top 3 reviews
                    result["reviews"].append({
                        "rating": review.get("rating", "N/A"),
                        "title": review.get("title", ""),
                        "date": review.get("date", ""),
                        "verified_purchase": review.get("verified_purchase", False),
                        "content": review.get("content", "")[:200]  # Limit content length
                    })

            return result

        except Exception as e:
            error_type = str(type(e).__name__)
            error_msg = str(e)

            # Handle specific error types
            if "blocked" in error_msg.lower() or "captcha" in error_msg.lower():
                logger.warning(f"Amazon blocking detected: {error_msg}")
                if attempt < max_retries - 1:
                    # Rotate proxy or user agent if available
                    if browser and hasattr(browser, "rotate_proxy"):
                        logger.info("Rotating proxy and trying again")
                        await browser.rotate_proxy()
                    # Wait before retry with exponential backoff
                    backoff_time = retry_delay * (2 ** attempt)
                    logger.info(f"Waiting {backoff_time}s before retry")
                    await asyncio.sleep(backoff_time)
                    continue
                return {"error": "Access temporarily blocked by Amazon. Please try again later."}

            # Network errors
            if any(err in error_msg.lower() for err in ["network", "timeout", "connection"]):
                logger.warning(f"Network error: {error_msg}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return {"error": f"Network error: {error_msg}. Please check your connection."}

            # General errors
            logger.error(f"Error getting product details ({error_type}): {error_msg}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return {"error": f"Failed to get product details: {error_msg}"}

    # If we get here, all retries failed
    return {"error": "Failed to get product details after multiple attempts."}

async def get_product_reviews(
    product_url: str,
    *,
    review_type: Optional[str] = None,
    max_reviews: int = 5,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Get customer reviews for a specific Amazon product.

    Args:
        product_url: The URL of the Amazon product
        review_type: Type of reviews to get ("positive", "critical", or None for all)
        max_reviews: Maximum number of reviews to return

    Returns:
        Product reviews with ratings, titles, and content
    """
    logger.info(f"Getting reviews for product: {product_url}")
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            # Get or create browser
            browser = await get_or_create_browser(config)

            logger.info(f"Fetching product reviews (attempt {attempt+1}/{max_retries})")
            details = await browser.get_product_details(product_url)
            all_reviews = await browser.get_product_reviews(product_url)

            # Filter reviews if review_type is specified
            filtered_reviews = all_reviews
            if review_type and all_reviews:
                if review_type.lower() == "positive":
                    filtered_reviews = [r for r in all_reviews if r.get("rating", "").startswith(("4", "5"))]
                elif review_type.lower() == "critical":
                    filtered_reviews = [r for r in all_reviews if r.get("rating", "").startswith(("1", "2", "3"))]

            # Format the response
            result = {
                "product_title": details.get("title", "Unknown"),
                "overall_rating": details.get("rating", "N/A"),
                "total_reviews": len(all_reviews),
                "reviews": []
            }

            # Add reviews
            for review in filtered_reviews[:max_reviews]:
                result["reviews"].append({
                    "rating": review.get("rating", "N/A"),
                    "title": review.get("title", ""),
                    "date": review.get("date", ""),
                    "verified_purchase": review.get("verified_purchase", False),
                    "content": review.get("content", ""),
                    "helpful_votes": review.get("helpful_votes", "0")
                })

            return result

        except Exception as e:
            error_type = str(type(e).__name__)
            error_msg = str(e)

            # Handle specific error types
            if "blocked" in error_msg.lower() or "captcha" in error_msg.lower():
                logger.warning(f"Amazon blocking detected: {error_msg}")
                if attempt < max_retries - 1:
                    # Rotate proxy or user agent if available
                    if browser and hasattr(browser, "rotate_proxy"):
                        logger.info("Rotating proxy and trying again")
                        await browser.rotate_proxy()
                    # Wait before retry with exponential backoff
                    backoff_time = retry_delay * (2 ** attempt)
                    logger.info(f"Waiting {backoff_time}s before retry")
                    await asyncio.sleep(backoff_time)
                    continue
                return {"error": "Access temporarily blocked by Amazon. Please try again later."}

            # Network errors
            if any(err in error_msg.lower() for err in ["network", "timeout", "connection"]):
                logger.warning(f"Network error: {error_msg}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return {"error": f"Network error: {error_msg}. Please check your connection."}

            # General errors
            logger.error(f"Error getting product reviews ({error_type}): {error_msg}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            return {"error": f"Failed to get product reviews: {error_msg}"}

    # If we get here, all retries failed
    return {"error": "Failed to get product reviews after multiple attempts."}

# List of available Amazon tools
AMAZON_TOOLS = [
    search_amazon_products,
    find_deals,
    compare_products,
    find_bestsellers,
    get_product_details,
    get_product_reviews
]


