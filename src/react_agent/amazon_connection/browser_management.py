"""Browser management module for Amazon connection.

This module centralizes browser pool management, rate limiting, and browser context handling
for Amazon connection operations.
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Forward reference for type checking
if TYPE_CHECKING:
    from .main import AmazonConnection

# Common user agents moved from utils.py
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55"
]

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

class BrowserPool:
    """Manages a pool of browser instances for reuse."""

    def __init__(self, max_browsers=3, ttl_seconds=300, cleanup_interval=60):
        self.browsers = []
        self.max_browsers = max_browsers
        self.ttl_seconds = ttl_seconds
        self.last_used = {}
        self.lock = asyncio.Lock()
        self.cleanup_task = None
        self.cleanup_interval = cleanup_interval

    async def start_cleanup_task(self):
        """Start the periodic cleanup task."""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self):
        """Periodically clean up expired browsers."""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            await self.cleanup_expired_browsers()

    async def cleanup_expired_browsers(self):
        """Clean up expired browsers."""
        async with self.lock:
            current_time = time.time()
            for browser_id in list(self.last_used.keys()):
                if current_time - self.last_used[browser_id] > self.ttl_seconds:
                    await self._close_browser(browser_id)

    async def get_browser(self, headless=True, slow_mo=50, proxy=None, proxies=None):
        """Get an available browser from the pool or create a new one."""
        from .main import AmazonConnection  # Import here to avoid circular imports

        async with self.lock:
            # Clean up expired browsers
            current_time = time.time()
            for browser_id in list(self.last_used.keys()):
                if current_time - self.last_used[browser_id] > self.ttl_seconds:
                    await self._close_browser(browser_id)

            # Check for available browser with matching config
            for i, browser_info in enumerate(self.browsers):
                browser, browser_config = browser_info
                if (browser_config["headless"] == headless and
                    browser_config["slow_mo"] == slow_mo and
                    browser_config["proxy"] == proxy):
                    # Update last used time
                    self.last_used[id(browser)] = current_time
                    return browser

            # Create new browser if under limit
            if len(self.browsers) < self.max_browsers:
                try:
                    browser = AmazonConnection(
                        headless=headless,
                        slow_mo=slow_mo,
                        proxy=proxy,
                        proxies=proxies
                    )
                    await browser.start()
                    self.browsers.append((browser, {
                        "headless": headless,
                        "slow_mo": slow_mo,
                        "proxy": proxy
                    }))
                    self.last_used[id(browser)] = current_time
                    return browser
                except Exception as e:
                    logger.error(f"Error creating browser: {str(e)}")
                    # If we can't create a new browser, try to reuse an existing one
                    if self.browsers:
                        browser, _ = self.browsers[0]
                        self.last_used[id(browser)] = current_time
                        return browser
                    raise  # Re-raise if we have no browsers at all

            # If at limit, reuse least recently used browser
            least_recent_id = min(self.last_used, key=self.last_used.get)
            for i, (browser, _) in enumerate(self.browsers):
                if id(browser) == least_recent_id:
                    try:
                        await browser.close()
                        new_browser = AmazonConnection(
                            headless=headless,
                            slow_mo=slow_mo,
                            proxy=proxy,
                            proxies=proxies
                        )
                        await new_browser.start()
                        self.browsers[i] = (new_browser, {
                            "headless": headless,
                            "slow_mo": slow_mo,
                            "proxy": proxy
                        })
                        self.last_used[id(new_browser)] = current_time
                        del self.last_used[least_recent_id]
                        return new_browser
                    except Exception as e:
                        logger.error(f"Error recreating browser: {str(e)}")
                        # Keep using the old browser if we can't create a new one
                        self.last_used[least_recent_id] = current_time
                        return browser

    async def _close_browser(self, browser_id):
        """Close and remove a browser from the pool."""
        for i, (browser, _) in enumerate(self.browsers):
            if id(browser) == browser_id:
                await browser.close()
                self.browsers.pop(i)
                del self.last_used[browser_id]
                break

    async def close_all(self):
        """Close all browsers in the pool."""
        for browser, _ in self.browsers:
            await browser.close()
        self.browsers = []
        self.last_used = {}

    async def get_or_create_browser(self, config: Dict[str, Any]) -> "AmazonConnection":
        """Get existing browser from config or create a new one using the pool."""
        browser = config.get("browser")

        if browser is None or not isinstance(browser, AmazonConnection):
            logger.info("Getting browser from pool")
            browser = await self.get_browser(
                headless=config.get("headless", True),
                slow_mo=config.get("browser_slow_mo", 50),
                proxy=config.get("browser_proxy", None),
                proxies=config.get("browser_proxies", None)
            )
            config["browser"] = browser
            config["browser_from_pool"] = True

        return browser

    async def close_browser_if_created(self, config: Dict[str, Any]) -> None:
        """Return browser to the pool if it was created by this tool."""
        if config.get("browser_from_pool") and config.get("browser"):
            logger.info("Returning browser to pool")
            # We don't actually close it, just remove the reference
            config["browser"] = None
            config["browser_from_pool"] = False

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
        self.browser = await browser_pool.get_or_create_browser(self.config)
        return self.browser

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Only close the browser if we're not in a chain of Amazon tool calls
        if not self.config.get("keep_browser_open"):
            await browser_pool.close_browser_if_created(self.config)

def amazon_tool(func):
    """Decorator for Amazon tool functions to handle common patterns."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract config from kwargs
        config = kwargs.get("config", {})

        # Use the browser context manager with the global rate_limiter
        async with BrowserContextManager(config, rate_limiter) as browser:
            # Add browser to kwargs for the function to use
            kwargs["browser"] = browser
            return await func(*args, **kwargs)

    return wrapper

# Create global instances
rate_limiter = RateLimiter()
browser_pool = BrowserPool()
