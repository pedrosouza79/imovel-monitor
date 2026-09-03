"""Ponto de entrada do monitor. Roda a busca em todos os sites ativos,
aplica os filtros do config.yaml, compara com o estado salvo (data/seen.json)
para achar o que é novo, atualiza o estado e gera a página HTML final.

Uso: python -m scraper.main
"""
import logging
import os

import yaml

from .render import render_html
from .state import load_state, mark_seen, prune_old, save_state
from .sites.dfimoveis import DfimoveisScraper
from .sites.imoveis61 import Imoveis61Scraper
from .sites.wimoveis import WimoveisScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

SCRAPERS = {
    "wimoveis": WimoveisScraper,
    "dfimoveis": DfimoveisScraper,
    "61imoveis": Imoveis61Scraper,
}


def load_config(path: str = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    filtros = config["filtros"]
    paginas = config.get("paginas_por_busca", 2)
    sites_ativos = config.get("sites_ativos", list(SCRAPERS.keys()))

    todos_encontrados = []
    for nome_site in sites_ativos:
        scraper_cls = SCRAPERS.get(nome_site)
        if not scraper_cls:
            logger.warning("Site desconhecido no config: %s", nome_site)
            continue
        logger.info("Buscando em %s...", nome_site)
        try:
            resultados = scraper_cls().search(filtros, paginas)
        except Exception:
            logger.exception("Falha ao buscar em %s, seguindo para o próximo site", nome_site)
            continue
        logger.info("%s: %d anúncios brutos encontrados", nome_site, len(resultados))
        todos_encontrados.extend(resultados)

    # aplica os filtros de preço/quartos/área (bairro já foi filtrado na busca)
    filtrados = [l for l in todos_encontrados if l.matches_filters(filtros)]

    # dedup por id, caso o mesmo anúncio apareça em mais de uma
    # combinação de bairro/página
    por_id = {}
    for l in filtrados:
        por_id[l.id] = l
    filtrados = list(por_id.values())

    logger.info("%d anúncios batem com os filtros (após dedup)", len(filtrados))

    state = load_state()
    novos = [l for l in filtrados if l.id not in state]
    logger.info("%d anúncios são novos desde a última execução", len(novos))

    for l in filtrados:
        mark_seen(state, l.id)
    state = prune_old(state, [l.id for l in filtrados])
    save_state(state)

    render_html(todos=filtrados, novos=novos)
    logger.info("Página gerada em docs/index.html")


if __name__ == "__main__":
    main()
