import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import random
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# --- Start: Original __del__ patch ---
# This patch addresses a potential OSError when uc.Chrome closes on some systems.
_original_del = uc.Chrome.__del__

def _safe_del(self):
    try:
        _original_del(self)
    except OSError:
        pass # Ignore the error

uc.Chrome.__del__ = _safe_del
# --- End: Original __del__ patch ---


class InstagramPostScraper:
    """
    Scrapes Instagram post likes by intercepting network requests.
    This class structure mirrors the logic of the original script.
    """
    def __init__(self, headless: bool = True, use_proxy: bool = False, proxies: list[str] | None = None, wait_time: int = 2):
        """
        Initializes the scraper configuration.
        Args:
            headless (bool): Whether to run the browser in headless mode.
        """
        self.headless = headless
        self.use_proxy = use_proxy
        self.proxies = proxies
        self.wait_time = wait_time
        # Driver instance is created within the get_likes method in this version
        # to strictly follow the original script's flow.

    def _extract_likes_from_json(self, payload: dict) -> int | None:
        """
        Extracts the number of likes from a given JSON object payload.
        Follows the exact structure check from the original script.
        Returns the count as int if found, otherwise None.
        """
        if "data" in payload:
            data = payload["data"]
            if "xdt_shortcode_media" in data:
                media_data = data["xdt_shortcode_media"]
                if "edge_media_preview_like" in media_data:
                    likes_data = media_data["edge_media_preview_like"]
                    if "count" in likes_data:
                        # Ensure returning an integer
                        try:
                            return int(likes_data['count'])
                        except (ValueError, TypeError):
                            return None # Return None if count is not a valid integer
        return None # Return None if the path does not exist

    def get_likes(self, url: str) -> int | None:
        """
        Attempts to get the like count for a given Instagram post URL.

        Args:
            url (str): The full URL of the Instagram post.

        Returns:
            int | None: The number of likes if found, otherwise None.
        """
        # 1. Enable performance logging (Original Capability Setup)
        caps = DesiredCapabilities.CHROME
        # Note: Using goog:loggingPrefs as in the original script
        caps["goog:loggingPrefs"] = {"performance": "ALL"}

        options = uc.ChromeOptions()
        options.headless = self.headless
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        # handler proxy
        if self.use_proxy:
            if self.proxies is None:
                raise ValueError("Proxy is required when use_proxy is True")
            else:
                options.add_argument(f"--proxy-server={self._get_proxy_random_from_list()}")
        driver = None # Define driver here to ensure it's available in finally block
        extracted_likes_count = None # Variable to store the result

        try:
            # Create the driver instance (as done in the original main function)
            driver = uc.Chrome(options=options, desired_capabilities=caps)

            # 2. Enable Network domain via CDP
            driver.execute_cdp_cmd("Network.enable", {})

            # 3. Navigate to the page
            logger.info(f"Navigating to: {url}")
            driver.get(url)

            # 4. Wait for XHR requests to load (Original fixed wait)
            logger.info(f"Waiting for {self.wait_time} seconds...")
            time.sleep(self.wait_time)

            # 5. Gather all performance logs
            # print("Gathering performance logs...") # Commented out direct print
            logs = driver.get_log("performance")

            logger.info(f"Gathering {len(logs)} performance logs...")
            for entry in logs:
                try:
                    message_str = entry.get("message", "{}")
                    message_data = json.loads(message_str)
                    message = message_data.get("message", {})
                except json.JSONDecodeError:
                    logger.info(f"Error decoding JSON: {message_str}")
                    continue # Skip malformed log entries

                # Only interested in specific network events (Original Filter)
                # IMPORTANT: This filter 'Network.requestWillBeSentExtraInfo' might not be
                # the most suitable for finding *response* data, but kept as per request.
                if message.get("method") != "Network.requestWillBeSentExtraInfo":
                    continue

                params = message.get("params", {})
                request_id = params.get("requestId")

                # The original script attempted to get response body using requestId from
                # 'requestWillBeSentExtraInfo'. This might be unreliable but is preserved here.
                if not request_id:
                    # print("Skipping entry: No requestId found.") # Commented out direct print
                    continue

                # 6. Retrieve response body via CDP for the captured requestId
                body_data = None
                try:
                     # print(f"Attempting to get response body for requestId: {request_id}") # Commented out direct print
                     body_data = driver.execute_cdp_cmd(
                         "Network.getResponseBody",
                         {"requestId": request_id}
                     )
                except Exception as cdp_error:
                    logger.error(f"CDP Error getting body for {request_id}: {cdp_error}")
                    continue # Skip if we cannot get the body

                body = body_data.get("body", "")
                if not body:
                    # print(f"No body content found for requestId: {request_id}") # Commented out direct print
                    continue # Skip if body is empty

                # 7. Parse JSON and extract xdt_shortcode_media (Original Logic)
                try:
                    # print(f"Attempting to parse JSON body for requestId: {request_id}") # Commented out direct print
                    payload = json.loads(body)
                    likes_value = self._extract_likes_from_json(payload) # Use the internal method

                    if likes_value is not None:
                        logging.info(f"Successfully extracted likes: {likes_value}")
                        extracted_likes_count = likes_value
                        break # Stop the loop after the first successful extraction (Original logic)


                except json.JSONDecodeError:
                    # print(f"Body for requestId {request_id} is not valid JSON.") # Commented out direct print
                    continue # Skip if JSON parsing fails (Original logic)

            # This part corresponds to the 'else' block of the original 'for' loop
            if extracted_likes_count is None:
                # This executes if the loop completed without a 'break' statement.
                # print("No suitable network response found containing likes count.") # Commented out direct print
                pass # No action needed here, will return None by default

        except Exception as e:
            # Catch broad exceptions as in the original main function
            # print(f"An unexpected error occurred during scraping: {e}") # Commented out direct print
            # Ensure function returns None in case of error
            extracted_likes_count = None

        finally:
            # print("Ensuring browser is closed...") # Commented out direct print
            if driver:
                try:
                    driver.quit()
                    logger.info("Browser closed.")
                except Exception as e:
                    logger.error(f"Error closing the driver: {e}")

        # Return the final result (either the count or None)
        return extracted_likes_count
    
    def _get_proxy_random_from_list(self) -> str:
        """
        Get a random proxy from the list of proxies.
        """
        return random.choice(self.proxies)