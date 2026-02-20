from __future__ import annotations
import requests
from typing import Any, Dict

def chat(host: str, model: str, messages, options: Dict[str, Any]):
    url = f"{host}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": options or {}
    }
    r = requests.post(url, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()