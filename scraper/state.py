"""Guarda quais anúncios já foram vistos, para identificar só os novos a
cada execução. O estado é um arquivo JSON simples versionado no git
(data/seen.json), o que permite que o GitHub Actions faça commit dele de
volta no repositório entre uma execução e outra.
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, List

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "seen.json")


def load_state(path: str = DEFAULT_PATH) -> Dict[str, dict]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_state(state: Dict[str, dict], path: str = DEFAULT_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


def mark_seen(state: Dict[str, dict], listing_id: str) -> None:
    state[listing_id] = {"first_seen": datetime.now(timezone.utc).isoformat()}


def prune_old(state: Dict[str, dict], keep_ids: List[str]) -> Dict[str, dict]:
    """Remove do estado anúncios que não apareceram na busca mais recente
    (provavelmente já foram vendidos/removidos), para o arquivo não crescer
    para sempre. Mantém só o que foi visto na última execução."""
    keep = set(keep_ids)
    return {k: v for k, v in state.items() if k in keep}
