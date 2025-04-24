import time
import json
import logging
import random
import requests
from datetime import datetime, timezone, timedelta
import undetected_chromedriver as uc

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class ProxySession:
    """
    Manages a headless Chrome session per proxy.
    Caches cookies and user-agent for a given TTL (default 24h).
    """
    TTL = timedelta(hours=24)

    def __init__(self, proxy: str, headless: bool, wait_time: int):
        self.proxy = proxy
        self.headless = headless
        self.wait_time = wait_time
        self.cookies: dict[str,str] = {}
        self.user_agent: str = ""
        self.expires_at: datetime = datetime.min

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    def refresh(self, url: str):
        """
        Launches an undetected_chromedriver, navigates to the URL,
        extracts cookies and user-agent, then closes the browser.
        """
        logger.info(f"Refreshing session for proxy {self.proxy}")
        options = uc.ChromeOptions()
        options.headless = self.headless
        options.add_argument(f"--proxy-server={self.proxy}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        # patch to avoid OSError on quit
        _original_del = uc.Chrome.__del__
        def _safe_del(self): 
            try: _original_del(self)
            except OSError: pass
        uc.Chrome.__del__ = _safe_del

        driver = uc.Chrome(options=options)
        try:
            driver.get(url)
            time.sleep(self.wait_time)
            # grab cookies and UA
            self.cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
            self.user_agent = driver.execute_script("return navigator.userAgent;")
            self.expires_at = datetime.now(timezone.utc) + ProxySession.TTL
        finally:
            try: driver.quit()
            except: pass

class InstagramPostScraper:
    """
    Scrapes Instagram post likes via the private GraphQL endpoint.
    Maintains a pool of ProxySession objects, keyed by proxy,
    each caching cookies+UA for 24h to speed up repeated calls.
    """

    GRAPHQL_URL = "https://www.instagram.com/graphql/query/"

    def __init__(self,
                 proxies: list[str],
                 headless: bool = True,
                 wait_time: int = 1):
        """
        Args:
          proxies: list of proxy server strings, e.g. ["http://ip:port", ...]
          headless: whether to run browser in headless mode
          wait_time: seconds to wait after page load to collect cookies
        """
        if not proxies:
            raise ValueError("At least one proxy must be provided")
        self.proxies = proxies
        self.headless = headless
        self.wait_time = wait_time
        # map proxy -> ProxySession
        self.sessions: dict[str, ProxySession] = {}

    def _get_session(self, proxy: str) -> ProxySession:
        """
        Return a valid (not expired) ProxySession for given proxy,
        refreshing it if needed.
        """
        sess = self.sessions.get(proxy)
        if sess is None or sess.is_expired():
            sess = ProxySession(proxy, self.headless, self.wait_time)
            # use a dummy post page to initialize cookies/UA
            sess.refresh(url="https://www.instagram.com/DIvhMZVIlmz/")
            self.sessions[proxy] = sess
        return sess

    def _fetch_likes_via_graphql(self, session: ProxySession, shortcode: str, proxy: str) -> int | None:
        """
        Uses requests.post with session.cookies and session.user_agent
        to call the Instagram GraphQL endpoint and parse exact like count.
        """
        # prepare headers and cookies
        headers = {
            "Accept": "*/*",
            "Accept-Language": "en",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.instagram.com",
            "Referer": f"https://www.instagram.com/p/{shortcode}/",
            "User-Agent": session.user_agent,
            "X-CSRFToken": session.cookies.get("csrftoken", ""),
            "X-IG-App-ID": "936619743392459",
        }
        payload = {
            "av": "0", "__d": "www", "__a": "1", "__user": "0", "__req": "b",
            "__hs": "", "dpr": "1", "__ccg": "GOOD", "__rev": "",
            "__s": "", "__hsi": "", "__dyn": "",
            "__csr": "", "__comet_req": "7", "lsd": "", "jazoest": "",
            "__spin_r": "", "__spin_b": "trunk", "__spin_t": "",
            "__crn": "", "fb_api_caller_class": "RelayModern",
            "fb_api_req_friendly_name": "PolarisPostActionLoadPostQueryQuery",
            "variables": json.dumps({
                "shortcode": shortcode,
                "fetch_tagged_user_count": None,
                "hoisted_comment_id": None,
                "hoisted_reply_id": None
            }),
            "server_timestamps": "true",
            "doc_id": "8845758582119845"
        }
        resp = requests.post(
            self.GRAPHQL_URL,
            headers=headers,
            cookies=session.cookies,
            data=payload,
            timeout=10,
            proxies={"https": proxy, "http": proxy}
        )
        if resp.status_code != 200:
            logger.error(f"GraphQL failed [{resp.status_code}]: {resp.text}")
            return None
        try:
            data = resp.json()
            return data["data"]["xdt_shortcode_media"]["edge_media_preview_like"]["count"]
        except Exception as e:
            logger.error(f"Parsing JSON failed: {e} / {resp.text}")
            return None

    def get_likes(self, shortcode: str) -> int | None:
        """
        Public method to get the like count for a given post shortcode.
        Selects a random proxy, obtains its session, then fetches via GraphQL.
        """
        proxy = random.choice(self.proxies)
        session = self._get_session(proxy)
        return self._fetch_likes_via_graphql(session, shortcode, proxy)

class InstagramUserScraper:
    """
    Fetches Instagram user profile data (including follower count)
    via the private web_profile_info endpoint. Uses ProxySession
    to reuse cookies and UA per proxy for 24h.
    """

    PROFILE_URL = "https://www.instagram.com/api/v1/users/web_profile_info/"

    def __init__(self,
                 proxies: list[str],
                 headless: bool = True,
                 wait_time: int = 1):
        """
        Args:
          proxies: list of proxy server strings, e.g. ["http://ip:port", ...]
          headless: whether to run browser in headless mode
          wait_time: seconds to wait after page load to collect cookies
        """
        if not proxies:
            raise ValueError("At least one proxy must be provided")
        self.proxies = proxies
        self.headless = headless
        self.wait_time = wait_time
        # map proxy -> ProxySession
        self.sessions: dict[str, ProxySession] = {}

    def _get_session(self, proxy: str) -> ProxySession:
        """
        Return a valid (not expired) ProxySession for given proxy,
        refreshing it if needed.
        """
        sess = self.sessions.get(proxy)
        if sess is None or sess.is_expired():
            sess = ProxySession(proxy, self.headless, self.wait_time)
            # hit a dummy page to initialize cookies/UA
            sess.refresh(url="https://www.instagram.com/")
            self.sessions[proxy] = sess
        return sess

    def get_user_info(self, username: str) -> dict | None:
        """
        Public method to fetch full user profile JSON for given username.
        Returns the 'user' object from the response, or None on failure.
        """
        proxy = random.choice(self.proxies)
        session = self._get_session(proxy)

        params = {"username": username}
        headers = {
            "Accept": "*/*",
            "Accept-Language": "en",
            "Referer": f"https://www.instagram.com/{username}/",
            "User-Agent": session.user_agent,
            "X-CSRFToken": session.cookies.get("csrftoken", ""),
            "X-IG-App-ID": "936619743392459",
            "X-Requested-With": "XMLHttpRequest",
        }

        resp = requests.get(
            self.PROFILE_URL,
            headers=headers,
            cookies=session.cookies,
            params=params,
            timeout=10,
            proxies={"https": proxy, "http": proxy}
        )

        if resp.status_code != 200:
            logger.error(f"Profile request failed [{resp.status_code}]: {resp.text}")
            return None

        try:
            data = resp.json()
            return data["data"]["user"]
        except Exception as e:
            logger.error(f"Error parsing profile JSON: {e}")
            return None

    def get_follower_count(self, username: str) -> int | None:
        """
        Convenience method to return only the follower count for a user.
        """
        user = self.get_user_info(username)
        if not user:
            return None
        # 'edge_followed_by' holds follower count
        return user.get("edge_followed_by", {}).get("count")