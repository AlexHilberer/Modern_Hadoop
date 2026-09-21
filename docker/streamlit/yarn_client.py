"""YARN ResourceManager cluster health, read directly off its REST API
(no auth needed)."""
import requests

from config import YARN_RM_URL


def get_yarn_nodes():
    try:
        resp = requests.get(f"{YARN_RM_URL}/ws/v1/cluster/nodes", timeout=5)
        resp.raise_for_status()
        return resp.json().get("nodes", {}).get("node", [])
    except requests.RequestException:
        return None
