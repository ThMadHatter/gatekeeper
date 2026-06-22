import json
import os
import httpx
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

REPO_FILE = "data/template_repos.json"

class RepoService:
    def __init__(self):
        self._ensure_repo_file()

    def _ensure_repo_file(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(REPO_FILE):
            with open(REPO_FILE, "w") as f:
                json.dump([
                    {"name": "Proxmox Official", "url": "http://download.proxmox.com/images/system/"},
                    {"name": "LinuxContainers.org", "url": "https://images.linuxcontainers.org/images/"}
                ], f)

    def list_repos(self) -> List[Dict[str, str]]:
        try:
            with open(REPO_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read repo file: {e}")
            return []

    async def add_repo(self, name: str, url: str) -> Dict[str, str]:
        # Validate URL
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.head(url, follow_redirects=True, timeout=10.0)
                if resp.status_code >= 400:
                    raise Exception(f"URL returned status {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to validate repo URL {url}: {e}")
            raise Exception(f"Invalid or unreachable template repository URL: {e}")

        repos = self.list_repos()
        if any(r["name"] == name for r in repos):
            raise Exception(f"Repo with name '{name}' already exists")

        new_repo = {"name": name, "url": url}
        repos.append(new_repo)

        try:
            with open(REPO_FILE, "w") as f:
                json.dump(repos, f)
            return new_repo
        except Exception as e:
            logger.error(f"Failed to write repo file: {e}")
            raise Exception(f"Failed to save repository: {e}")

    def remove_repo(self, name: str):
        repos = self.list_repos()
        filtered_repos = [r for r in repos if r["name"] != name]

        if len(repos) == len(filtered_repos):
            raise Exception(f"Repo '{name}' not found")

        try:
            with open(REPO_FILE, "w") as f:
                json.dump(filtered_repos, f)
        except Exception as e:
            logger.error(f"Failed to write repo file: {e}")
            raise Exception(f"Failed to update repository list: {e}")

    def get_repo_by_name(self, name: str) -> Dict[str, str]:
        repos = self.list_repos()
        for repo in repos:
            if repo["name"] == name:
                return repo
        raise Exception(f"Repository '{name}' not found")
