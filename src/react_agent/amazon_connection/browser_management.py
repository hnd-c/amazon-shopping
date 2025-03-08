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
from playwright.async_api import async_playwright, Browser as PlaywrightBrowser, BrowserContext, Page, Playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Forward reference for type checking
if TYPE_CHECKING:
    from .main import AmazonConnection

#######################################
# Common Constants
#######################################

# Common user agents moved from utils.py
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55"
]

#######################################
# Base Browser Class
#######################################

class Browser:
    """Base browser class that handles common browser operations."""

    def __init__(self, headless: bool = True, slow_mo: int = 50, proxy: Optional[str] = None, proxies: Optional[List[str]] = None):
        """Initialize the browser.

        Args:
            headless: Whether to run the browser in headless mode
            slow_mo: Slow down operations by this amount of milliseconds
            proxy: Single proxy to use (format: "http://user:pass@host:port")
            proxies: List of proxies to rotate through
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.proxy = proxy
        self.proxies = proxies
        self.current_proxy_index = 0
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.user_agent = None

    # Lifecycle methods
    async def __aenter__(self):
        """Set up the connection when entering a context."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting a context."""
        await self.close()

    async def start(self):
        """Start the browser and create a new context."""
        logger.info("Starting browser")
        self.playwright = await async_playwright().start()

        # Launch with more stealth options
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-web-security',
                '--disable-features=BlockInsecurePrivateNetworkRequests'
            ]
        )

        # Create a context with a random user agent and more realistic settings
        await self.setup_stealth_browser()

        # Create a page
        self.page = await self.context.new_page()

        # Add human-like behavior AFTER page is created
        await self._add_human_behavior()

        logger.info(f"Browser started with user agent: {self.user_agent}")

    async def close(self):
        """Close the browser and clean up resources."""
        if self.page:
            await self.page.close()
            self.page = None

        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        logger.info("Browser closed")

    # Stealth and anti-detection methods
    async def setup_stealth_browser(self):
        """Set up a browser context with stealth settings to avoid detection."""
        # Select a random user agent
        self.user_agent = random.choice(USER_AGENTS)

        # Set up proxy if provided
        proxy_settings = None
        if self.proxies and len(self.proxies) > 0:
            # Rotate through available proxies
            self.proxy = self.proxies[self.current_proxy_index % len(self.proxies)]
            self.current_proxy_index += 1

        if self.proxy:
            logger.info(f"Using proxy: {self.proxy.split('@')[-1]}")  # Log only the host part for security
            proxy_settings = {"server": self.proxy}

        # Create a context with the selected user agent and realistic viewport
        self.context = await self.browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},
            proxy=proxy_settings,
            java_script_enabled=True,
            locale="en-US",
            timezone_id="America/New_York",
            has_touch=False,
            is_mobile=False,
            device_scale_factor=1,
            color_scheme="light"
        )

        # Add additional scripts to avoid detection
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });

            // Overwrite the plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // Overwrite the languages property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)

    async def _add_human_behavior(self):
        """Add human-like behavior to avoid detection."""
        # Add random mouse movements
        await self.page.evaluate("""
            () => {
                const randomMove = () => {
                    const x = Math.floor(Math.random() * window.innerWidth);
                    const y = Math.floor(Math.random() * window.innerHeight);
                    const event = new MouseEvent('mousemove', {
                        'view': window,
                        'bubbles': true,
                        'cancelable': true,
                        'clientX': x,
                        'clientY': y
                    });
                    document.dispatchEvent(event);
                };

                // Random mouse movements
                setInterval(randomMove, Math.floor(Math.random() * 5000) + 2000);
            }
        """)

    async def _route_handler(self, route, request):
        """Handle requests to modify headers and block unnecessary resources."""
        # Block unnecessary resources to improve performance
        if request.resource_type in ["image", "media", "font"]:
            if random.random() < 0.7:  # Allow some resources to load for better stealth
                await route.abort()
                return

        # Add additional headers for stealth
        headers = {
            **request.headers,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }

        await route.continue_(headers=headers)

    async def rotate_proxy(self):
        """Rotate to a new proxy and recreate the browser context."""
        if not self.proxies:
            logger.warning("No proxies available for rotation")
            return False

        logger.info("Rotating proxy...")

        # Close existing context and page
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()

        # Create new context with next proxy
        await self.setup_stealth_browser()

        # Create new page
        self.page = await self.context.new_page()

        # Add human-like behavior
        await self._add_human_behavior()

        logger.info(f"Proxy rotated, new user agent: {self.user_agent}")
        return True

    # Navigation and interaction methods
    async def _navigate_with_retry(self, url, max_retries=3, retry_delay=2):
        """Navigate to a URL with retry logic."""
        for attempt in range(max_retries):
            try:
                response = await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Check if we got a valid response
                if response and response.ok:
                    # Add a small delay to ensure page is interactive
                    await asyncio.sleep(random.uniform(1.0, 2.0))
                    return response

                # Check for 503 error or CAPTCHA
                if response and response.status == 503:
                    logger.warning(f"503 Service Unavailable detected on attempt {attempt+1}")

                    # Try to rotate proxy if available
                    if self.proxies and len(self.proxies) > 0:
                        logger.info("Rotating proxy due to 503 error")
                        await self.rotate_proxy()

                    if attempt < max_retries - 1:
                        # Add increasing delay between retries
                        delay = retry_delay * (attempt + 1) * (1 + random.random())
                        logger.info(f"Waiting {delay:.2f}s before retry")
                        await asyncio.sleep(delay)
                        continue

                # Check for CAPTCHA
                for captcha_selector in ["input[name='amzn-captcha-submit']", "img[src*='captcha']"]:
                    if await self.page.query_selector(captcha_selector):
                        logger.warning(f"CAPTCHA detected on attempt {attempt+1}")

                        # Try to rotate proxy if available
                        if self.proxies and len(self.proxies) > 0:
                            logger.info("Rotating proxy due to CAPTCHA")
                            await self.rotate_proxy()

                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue
                        raise Exception("CAPTCHA detected")

                # If we got here, we have a non-OK response
                logger.warning(f"Navigation failed with status: {response.status if response else 'No response'}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue

                raise Exception(f"Failed to navigate to {url} after {max_retries} attempts")

            except Exception as e:
                logger.warning(f"Navigation error on attempt {attempt+1}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                raise

    # Element interaction methods
    async def _wait_for_element(self, selector, timeout=10000):
        """Wait for an element to be present on the page."""
        try:
            return await self.page.wait_for_selector(selector, timeout=timeout)
        except Exception as e:
            logger.warning(f"Timeout waiting for selector: {selector}")
            return None

    async def _get_text(self, selector, default=""):
        """Get text content from an element."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                return (await element.text_content()).strip()
            return default
        except Exception as e:
            logger.debug(f"Error getting text for {selector}: {str(e)}")
            return default

    async def _get_attribute(self, selector, attribute, default=""):
        """Get attribute value from an element."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                attr_value = await element.get_attribute(attribute)
                return attr_value.strip() if attr_value else default
            return default
        except Exception as e:
            logger.debug(f"Error getting attribute {attribute} for {selector}: {str(e)}")
            return default

#######################################
# Browser Pool Management
#######################################

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
        # Import here to avoid circular imports
        from .main import AmazonConnection

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
                    if proxies and len(proxies) > 0:
                        # Rotate through proxies for each new browser
                        proxy = proxies[random.randint(0, len(proxies)-1)]
                        logger.info(f"Using proxy: {proxy}")

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

#######################################
# Utility Classes
#######################################

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

#######################################
# Decorators
#######################################

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

#######################################
# Global Instances
#######################################

# Create global instances
rate_limiter = RateLimiter()
browser_pool = BrowserPool()
