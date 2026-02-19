import os
import random
from typing import List, Optional

class ProxyRotator:
    def __init__(self, env_file: str = ".env"):
        self.base_dir = os.path.dirname(env_file)
        self.index_file = os.path.join(self.base_dir, ".index")
        self.proxies: List[str] = []
        self.load_proxies(env_file)

    def _get_stored_index(self) -> int:
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r") as f:
                    return int(f.read().strip())
            except:
                pass
        return 0

    def _save_index(self, index: int):
        with open(self.index_file, "w") as f:
            f.write(str(index))

    def load_proxies(self, env_file: str):
        """Loads proxies from the .env file."""
        if not os.path.exists(env_file):
            return

        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("PROXY_LIST="):
                    proxy_str = line.split("=", 1)[1]
                    # Filter and clean proxies
                    self.proxies = [p.strip() for p in proxy_str.split(",") if p.strip()]
                    break

    def get_next_proxy(self) -> Optional[str]:
        """Returns the next proxy in the list (round-robin)."""
        if not self.proxies:
            return None
        
        index = self._get_stored_index()
        # Ensure index is within current list bounds
        index = index % len(self.proxies)
        
        proxy = self.proxies[index]
        
        # Save next index
        next_index = (index + 1) % len(self.proxies)
        self._save_index(next_index)
        
        return proxy

if __name__ == "__main__":
    # Test block
    rotator = ProxyRotator(os.path.join(os.path.dirname(__file__), ".env"))
    next_p = rotator.get_next_proxy()
    if next_p:
        print(f"Next proxy: {next_p}")
    else:
        print("No proxies configured in proxy/.env")
