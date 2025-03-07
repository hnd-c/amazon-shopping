"""Utility functions and constants for Amazon connection."""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Dict, Optional, TypedDict

logger = logging.getLogger(__name__)

# Define standard return types
class ProductInfo(TypedDict):
    title: str
    price: str
    url: str
    asin: str
    prime_eligible: bool
    rating: Optional[str]
    review_count: Optional[str]
    availability: Optional[str]
    delivery_info: Optional[str]

class ErrorResponse(TypedDict):
    error: str
    error_type: Optional[str]
    success: bool

class RateLimiter:
    """Implements rate limiting for Amazon requests."""

    def __init__(self, requests_per_minute=20):
        self.requests_per_minute = requests_per_minute
        self.interval = 60 / requests_per_minute  # seconds between requests
        self.last_request_time = 0
        self.lock = asyncio.Lock()

    async def wait(self):
        """Wait if necessary to comply with rate limits."""
        async with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time

            if elapsed < self.interval:
                wait_time = self.interval - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

            self.last_request_time = time.time()

# Create a standardized error response function
def create_error_response(error_message, error_type=None, additional_info=None):
    """Create a standardized error response."""
    response = {
        "error": error_message,
        "success": False
    }

    if error_type:
        response["error_type"] = error_type

    if additional_info:
        response["additional_info"] = additional_info

    return response

# Create a retry decorator
def with_retry(max_retries=3, retry_delay=2):
    """Decorator to add retry logic to Amazon tool functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    error_type = str(type(e).__name__)
                    error_msg = str(e)

                    # Handle specific error types
                    if "blocked" in error_msg.lower() or "captcha" in error_msg.lower():
                        logger.warning(f"Amazon blocking detected: {error_msg}")
                        if attempt < max_retries - 1:
                            # Rotate proxy if available
                            config = kwargs.get("config", {})
                            browser = config.get("browser")
                            if browser and hasattr(browser, "rotate_proxy"):
                                logger.info("Rotating proxy and trying again")
                                await browser.rotate_proxy()
                            # Wait before retry with exponential backoff
                            backoff_time = retry_delay * (2 ** attempt)
                            logger.info(f"Waiting {backoff_time}s before retry")
                            await asyncio.sleep(backoff_time)
                            continue
                        return create_error_response(
                            "Access temporarily blocked by Amazon. Please try again later.",
                            error_type="AccessBlocked"
                        )

                    # Network errors
                    if any(err in error_msg.lower() for err in ["network", "timeout", "connection"]):
                        logger.warning(f"Network error: {error_msg}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        return create_error_response(
                            f"Network error: {error_msg}. Please check your connection.",
                            error_type="NetworkError"
                        )

                    # General errors
                    logger.error(f"Error in {func.__name__} ({error_type}): {error_msg}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                    return create_error_response(
                        f"Operation failed: {error_msg}",
                        error_type=error_type
                    )

            return create_error_response(
                "Failed after multiple attempts.",
                error_type="RetryLimitExceeded"
            )
        return wrapper
    return decorator

# Define robust selectors as constants
SELECTORS = {
    # Search results
    "search_results_container": "div.s-result-list, div.s-search-results",
    "product_card": "div.s-result-item[data-component-type='s-search-result'], div.sg-col-4-of-24",
    "product_title": "h2 a span, h2 span, .a-text-normal",
    "product_price": ".a-price .a-offscreen, span.a-price, .a-color-price",
    "product_rating": ".a-icon-star-small .a-icon-alt, .a-icon-star .a-icon-alt",
    "prime_badge": "i.a-icon-prime",

    # Product details
    "product_title_detail": "#productTitle",
    "product_price_detail": "#priceblock_ourprice, #priceblock_dealprice, .a-price .a-offscreen",
    "product_availability": "#availability",
    "product_features": "#feature-bullets li:not(.aok-hidden) span.a-list-item",
    "product_description": "#productDescription p",
    "product_rating_detail": "#acrPopover",
    "product_review_count": "#acrCustomerReviewText",
    "product_images": "#altImages img",
    "delivery_info": "div[data-hook='delivery-block']",

    # Reviews
    "review_container": "#customerReviews .review, [data-hook='review']",
    "review_rating": "i[data-hook='review-star-rating'], .a-icon-star",
    "review_title": "a[data-hook='review-title'], span[data-hook='review-title']",
    "review_date": "span[data-hook='review-date']",
    "review_verified": "span[data-hook='avp-badge']",
    "review_content": "span[data-hook='review-body'] span:not(script)",
    "review_helpful": "span[data-hook='helpful-vote-statement']",

    # CAPTCHA detection
    "captcha_selectors": [
        "form[action='/errors/validateCaptcha']",
        "input[name='amzn-captcha-submit']",
        "img[src*='captcha']",
        "input[id='captchacharacters']"
    ]
}

# Common user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55"
]

class BrowserContextManager:
    """Context manager for handling browser lifecycle in tool functions."""

    def __init__(self, config, rate_limiter):
        self.config = config
        self.rate_limiter = rate_limiter
        self.browser = None

    async def __aenter__(self):
        # Wait for rate limiter
        await self.rate_limiter.wait()

        # Get or create browser
        from .main import browser_pool
        self.browser = await browser_pool.get_or_create_browser(self.config)
        return self.browser

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Only close the browser if we're not in a chain of Amazon tool calls
        if not self.config.get("keep_browser_open"):
            from .main import browser_pool
            await browser_pool.close_browser_if_created(self.config)