"""Scraper do 61imoveis.com.

Diferente do wimoveis e do dfimoveis, este site carrega a lista de anúncios
via JavaScript depois que a página abre (é uma SPA) — o HTML inicial só tem
o esqueleto da página com um spinner de "carregando". Por isso usamos o
Playwright (navegador headless) para abrir a página de verdade, esperar o
JS rodar e só então ler o HTML final.

Isso deixa esse scraper mais lento e mais pesado que os outros dois — é
esperado. No GitHub Actions, o Playwright + Chromium é instalado no próprio
workflow (veja .github/workflows/monitor.yml).
"""
import logging
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from ..models import Listing
from ..parsing_utils import parse_area, parse_preco, parse_quartos
from .base import SiteScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://www.61imoveis.com"


class Imoveis61Scraper(SiteScraper):
    name = "61imoveis"

    def search(self, filtros: dict, paginas: int) -> List[Listing]:
        # Import feito aqui dentro para que o resto do projeto não quebre
        # caso o Playwright não esteja instalado (ex: rodando só
        # wimoveis/dfimoveis localmente).
        from playwright.sync_api import sync_playwright

        negocio = filtros.get("negocio", "venda")
        cidade = filtros.get("cidade", "brasilia")
        tipo = filtros.get("tipo", "apartamento")
        bairros = filtros.get("bairros") or [None]
        resultados: List[Listing] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                )
            )

            for bairro in bairros:
                url = self._montar_url(negocio, cidade, bairro, tipo)
                try:
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    # espera os cards de anúncio aparecerem; se não aparecer
                    # em 15s, segue em frente com o que tiver na página
                    page.wait_for_selector('a[href*="/imovel/"]', timeout=15000)
                except Exception as exc:  # noqa: BLE001 - queremos seguir mesmo se falhar
                    logger.warning("61imoveis: falha/timeout em %s (%s)", url, exc)

                html = page.content()
                soup = BeautifulSoup(html, "lxml")
                cards = self._find_cards(soup)
                for card in cards:
                    listing = self._parse_card(card)
                    if listing:
                        if bairro:
                            listing.bairro = listing.bairro or bairro
                        resultados.append(listing)

            browser.close()

        return resultados

    def _montar_url(self, negocio: str, cidade: str, bairro: Optional[str], tipo: str) -> str:
        if bairro:
            return f"{BASE_URL}/{negocio}/{tipo}/{cidade}/{bairro}"
        return f"{BASE_URL}/{negocio}/{tipo}/{cidade}"

    def _find_cards(self, soup: BeautifulSoup):
        anchors = soup.select('a[href*="/imovel/"]')
        cards = []
        seen_hrefs = set()
        for a in anchors:
            href = a.get("href")
            if not href or href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            node = a
            for _ in range(6):
                if node.parent is None:
                    break
                node = node.parent
                if "quarto" in node.get_text().lower():
                    cards.append((href, node))
                    break
        return cards

    def _parse_card(self, card) -> Optional[Listing]:
        href, node = card
        texto = node.get_text(separator=" ", strip=True)

        listing_id_match = re.search(r"/(\d+)/?$", href)
        listing_id = listing_id_match.group(1) if listing_id_match else href

        url = href if href.startswith("http") else BASE_URL + href

        img = node.find("img")
        image_url = img.get("src") if img else None

        titulo_tag = node.find(["h1", "h2", "h3"])
        titulo = titulo_tag.get_text(strip=True) if titulo_tag else texto[:100]

        return Listing(
            id=f"61imoveis:{listing_id}",
            source="61imoveis",
            title=titulo,
            url=url,
            price=parse_preco(texto),
            bairro=None,
            quartos=parse_quartos(texto),
            area_m2=parse_area(texto),
            image_url=image_url,
        )
