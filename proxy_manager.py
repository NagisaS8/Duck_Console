import json
import requests
import variables
import random
from tqdm import tqdm 

class Manager:
    def __init__(self, proxypool_path: str, max_requests_per_proxy: int, update_threshold=10) -> None:
        self.proxypool_file = proxypool_path
        self.max_requests = max_requests_per_proxy
        self.pool = []
        self.candidates = []
        self.root_proxy_addr = ""
        self.update_threshold = update_threshold
        self.used_proxy = 0
        
        # Get the root proxy for proxy API requests.
        self._get_root_proxy()

    def _get_root_proxy(self):
        """
        Retrieves the root proxy to use for API requests.
        """
        self._load_pool()
        self.root_proxy_addr = {"http": random.choice(self.pool)["Address"] if self.pool else ""}

    def update_pool(self) -> None:
        """
        Updates the proxy pool by removing overused or invalid proxies.
        If the pool is insufficient, fetches new candidates and validates them.
        Displays a progress bar when processing new candidates.
        """
        self._load_pool()
        poollen = len(self.pool)

        if not poollen < 2:
            for i, proxy in enumerate(self.pool):
                if proxy["UsageCount"] < self.max_requests and self._check_proxy_validity(proxy["Address"]):
                    self.pool[i]["Usable"] = True
                else:
                    del self.pool[i]
        if poollen < 2:
            self._fetch_candidates()
            new_pool = []
            
            # Use tqdm to show a progress bar as we validate each candidate
            for candidate in tqdm(self.candidates, desc="Updating Proxies", unit="proxy"):
                if self._check_proxy_validity(candidate.strip()):
                    new_pool.append({
                        "Address": candidate,
                        "UsageCount": 0,
                        "Usable": True
                    })
            self.pool = new_pool
        
        self._save_pool()

    def request_proxy(self) -> dict:
        """
        Returns a usable proxy from the pool after updating the pool.
        """
        self.used_proxy += 1
        if len(self.pool) < 2:
            self.update_pool()
            self.used_proxy = 0
        if self.used_proxy >= self.update_threshold:
            self.update_pool()
            self.used_proxy = 0

        proxy = self._get_random_proxy()
        proxy_id = self.pool.index(proxy)
        self.pool[proxy_id]["UsageCount"] += 1

        if not self._check_proxy_validity(proxy["Address"]):
            proxy = self.request_proxy()

        return self._format_proxy(proxy)
    
    def _get_random_proxy(self):
        proxy = random.choice(self.pool)

        if proxy["Usable"] == False:
            proxy = self._get_random_proxy()
        
        return proxy

    def _format_proxy(self, proxy: dict) -> dict:
        """
        Formats the proxy address for use in requests.
        """
        return {"http": "http://" + proxy["Address"].strip()}

    def _fetch_candidates(self):
        """
        Fetches new proxy candidates from the API and stores them.
        """
        parameters = {
            "request": "displayproxies",
            "protocol": "http",
            "timeout": "10000",
            "country": "all",
            "ssl": "all",
            "anonymity": "elite"
        }

        # Request new proxy candidates using the root proxy
        if self.root_proxy_addr != "":
            candidates_string = requests.get(variables.PROXYSCRAPE_API_URL, params=parameters, proxies=self.root_proxy_addr).text
        else:
            candidates_string = requests.get(variables.PROXYSCRAPE_API_URL, params=parameters).text
        candidate_list = candidates_string.split('\n')
        self.candidates = candidate_list

    def _load_pool(self):
        """
        Loads the proxy pool from a file.
        If the file is empty or unreadable, initializes an empty pool.
        """
        try:
            with open(self.proxypool_file, 'r') as pool:
                self.pool = json.load(pool)
        except:
            self.pool = []

    def _check_proxy_validity(self, address: str) -> bool:
        """
        Checks if a proxy is valid by making a test request.
        """
        try:
            for i in range(5):
                requests.get(variables.PROXY_TEST_URL, proxies={"http": address}, timeout=0.3)
            is_valid = True
        except:
            is_valid = False
        
        return is_valid

    def _save_pool(self):
        """
        Saves the current proxy pool to a file.
        """
        with open(self.proxypool_file, 'w') as pool:
            json.dump(self.pool, pool)

#XXX: Note that some of the proxy servers get blocked.