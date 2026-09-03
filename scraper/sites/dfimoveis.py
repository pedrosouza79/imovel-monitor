"""Scraper do dfimoveis.com.br.

Assim como o wimoveis, o HTML já vem com os anúncios renderizados, então
requests + BeautifulSoup é suficiente.
"""
import logging
import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from ..models import Listing
from ..parsing_utils import parse_area, parse_preco, parse_quartos
from .base import SiteScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.dfimoveis.com.br"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


class DfimoveisScraper(SiteScraper):
    name = "dfimoveis"

    def search(self, filtros: dict, paginas: int) -> List[Listing]:
        negocio = filtros.get("negocio", "venda")
        cidade = filtros.get("cidade", "brasilia")
        tipo = filtros.get("tipo", "apartamento")
        bairros = filtros.get("bairros") or [None]
        resultados: List[Listing] = []

        for bairro in bairros:
            url_base = self._montar_url(negocio, cidade, bairro, tipo)
            for pagina in range(1, paginas + 1):
                url = url_base if pagina == 1 else f"{url_base}?pagina={pagina}"
                try:
                    resp = requests.get(url, headers=HEADERS, timeout=20)
                    resp.raise_for_status()
                except requests.RequestException as exc:
                    logger.warning("dfimoveis: falha ao buscar %s (%s)", url, exc)
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                cards = self._find_cards(soup)
                if not cards:
                    break
                for card in cards:
                    listing = self._parse_card(card)
                    if listing:
                        if bairro:
                            listing.bairro = listing.bairro or bairro
                        resultados.append(listing)

        return resultados

    def _montar_url(self, negocio: str, cidade: str, bairro: Optional[str], tipo: str) -> str:
        if bairro:
            return f"{BASE_URL}/{negocio}/df/{cidade}/{bairro}/{tipo}"
        return f"{BASE_URL}/{negocio}/df/{cidade}/{tipo}"

    def _find_cards(self, soup: BeautifulSoup):
        anchors = soup.select('a[href*="/imovel/"]')
        cards = []
        seen_hrefs = set()
        for a in anchors:
            href = a.get("href")
            if not href or href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            texto = a.get_text(separator=" ", strip=True)
            if "R$" in texto or "Consulta" in texto:
                cards.append((href, a))
        return cards

    def _parse_card(self, card) -> Optional[Listing]:
        href, node = card
        texto = node.get_text(separator=" ", strip=True)

        listing_id_match = re.search(r"-(\d+)$", href.rstrip("/"))
        listing_id = listing_id_match.group(1) if listing_id_match else href

        url = href if href.startswith("http") else BASE_URL + href

        img = node.find("img")
        image_url = img.get("src") if img else None

        return Listing(
            id=f"dfimoveis:{listing_id}",
            source="dfimoveis",
            title=texto[:100],
            url=url,
            price=parse_preco(texto),
            bairro=None,
            quartos=parse_quartos(texto),
            area_m2=parse_area(texto),
            image_url=image_url,
        )
