"""Funções auxiliares para extrair números de textos em português brasileiro,
usadas pelos parsers de cada site. Ficam centralizadas aqui porque o formato
de preço/área/quartos é parecido nos 3 sites (ex: "R$ 1.200.000", "80 m²",
"3 Quartos").
"""
import re
from typing import Optional

_PRECO_RE = re.compile(r"R\$\s*([\d.,]+)")
_AREA_RE = re.compile(r"([\d.,]+)\s*m²")
_QUARTOS_RE = re.compile(r"(\d+)\s*(?:a\s*\d+\s*)?[Qq]uart")


def parse_preco(texto: str) -> Optional[float]:
    """Extrai o primeiro valor em R$ de um texto. Retorna None se não achar
    ou se for um preço "sob consulta" / "a partir de" sem número claro."""
    if not texto:
        return None
    match = _PRECO_RE.search(texto)
    if not match:
        return None
    valor = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return None


def parse_area(texto: str) -> Optional[float]:
    if not texto:
        return None
    match = _AREA_RE.search(texto)
    if not match:
        return None
    valor = match.group(1).replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return None


def parse_quartos(texto: str) -> Optional[int]:
    if not texto:
        return None
    match = _QUARTOS_RE.search(texto)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None
