"""Scraper do wimoveis.com.br.

O site renderiza os anúncios direto no HTML (server-side), então dá pra
raspar com requests + BeautifulSoup, sem precisar de navegador.

NOTA IMPORTANTE: os seletores abaixo foram construídos a partir de uma
amostra do HTML do site (visto em [DATA]). Sites de imóveis mudam de layout
de vez em quando — se o scraper parar de encontrar anúncios, o primeiro
lugar para olhar é a função `_parse_card`: rode `debug_dump_html()` (veja
final do arquivo) para salvar uma amostra do HTML atual e comparar.
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

BASE_URL = "https://www.wimoveis.com.br"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


class WimoveisScraper(SiteScraper):
    name = "wimoveis"

    def search(self, filtros: dict, paginas: int) -> List[Listing]:
        negocio = filtros.get("negocio", "venda")
        bairros = filtros.get("bairros") or [None]
        resultados: List[Listing] = []

        for bairro in bairros:
            url_base = self._montar_url(negocio, filtros.get("cidade", "brasilia"), bairro)
            for pagina in range(1, paginas + 1):
                url = url_base if pagina == 1 else f"{url_base}?pagina={pagina}"
                try:
                    resp = requests.get(url, headers=HEADERS, timeout=20)
                    resp.raise_for_status()
                except requests.RequestException as exc:
                    logger.warning("wimoveis: falha ao buscar %s (%s)", url, exc)
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                cards = self._find_cards(soup)
                if not cards:
                    break  # provavelmente não há mais páginas de resultado
                for card in cards:
                    listing = self._parse_card(card)
                    if listing:
                        if bairro:
                            listing.bairro = listing.bairro or bairro
                        resultados.append(listing)

        return resultados

    def _montar_url(self, negocio: str, cidade: str, bairro: Optional[str]) -> str:
        partes = [BASE_URL, negocio, "apartamentos", "df", cidade]
        if bairro:
            partes.append(bairro)
        return "/".join(partes)

    def _find_cards(self, soup: BeautifulSoup):
        # Cada anúncio tem um link para /propriedades/<slug>-<id>.html
        anchors = soup.select('a[href*="/propriedades/"]')
        cards = []
        seen_hrefs = set()
        for a in anchors:
            href = a.get("href")
            if not href or href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            # sobe na árvore até achar um bloco que pareça o card inteiro
            # (contém "R$" no texto), até no máximo 6 níveis acima
            node = a
            for _ in range(6):
                if node.parent is None:
                    break
                node = node.parent
                if "R$" in node.get_text():
                    cards.append((href, node))
                    break
        return cards

    def _parse_card(self, card) -> Optional[Listing]:
        href, node = card
        texto = node.get_text(separator=" ", strip=True)

        listing_id_match = re.search(r"-(\d+)\.html", href)
        listing_id = listing_id_match.group(1) if listing_id_match else href

        url = href if href.startswith("http") else BASE_URL + href

        img = node.find("img")
        image_url = img.get("src") if img else None

        titulo_tag = node.find(["h2", "h3"])
        titulo = titulo_tag.get_text(strip=True) if titulo_tag else texto[:80]

        return Listing(
            id=f"wimoveis:{listing_id}",
            source="wimoveis",
            title=titulo,
            url=url,
            price=parse_preco(texto),
            bairro=None,
            quartos=parse_quartos(texto),
            area_m2=parse_area(texto),
            image_url=image_url,
        )


def debug_dump_html(url: str, out_path: str = "debug_wimoveis.html") -> None:
    """Utilitário manual: salva o HTML bruto de uma URL de busca para
    inspecionar seletores quando o site mudar de layout."""
    resp = requests.get(url, headers=HEADERS, timeout=20)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(resp.text)
