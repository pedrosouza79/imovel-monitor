"""Gera a página HTML estática (docs/index.html) mostrando os anúncios
novos e o restante dos anúncios que batem com os filtros. Essa pasta docs/
é a fonte configurada no GitHub Pages para o site do projeto.
"""
import os
from datetime import datetime, timezone
from typing import List

from jinja2 import Template

from .models import Listing

TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Monitor de Apartamentos - Brasília</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; max-width: 1000px; margin: 0 auto; padding: 24px; background: #f7f7f8; color: #1a1a1a; }
  h1 { font-size: 1.6rem; margin-bottom: 4px; }
  .meta { color: #666; font-size: 0.9rem; margin-bottom: 24px; }
  .section-title { margin-top: 32px; font-size: 1.2rem; border-bottom: 2px solid #ddd; padding-bottom: 6px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; margin-top: 16px; }
  .card { background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.12); display: flex; flex-direction: column; }
  .card.novo { outline: 2px solid #2e7d32; }
  .card img { width: 100%; height: 160px; object-fit: cover; background: #eee; }
  .card-body { padding: 12px 14px; flex: 1; display: flex; flex-direction: column; gap: 4px; }
  .badge { display: inline-block; background: #2e7d32; color: white; font-size: 0.7rem; padding: 2px 8px; border-radius: 999px; margin-bottom: 6px; width: fit-content; }
  .source { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; color: #888; }
  .title { font-size: 0.95rem; font-weight: 600; line-height: 1.3; }
  .price { font-size: 1.05rem; font-weight: 700; color: #1a1a1a; }
  .details { font-size: 0.85rem; color: #555; }
  a.card-link { text-decoration: none; color: inherit; }
  .empty { color: #777; margin-top: 12px; }
</style>
</head>
<body>
  <h1>Monitor de Apartamentos — Brasília</h1>
  <div class="meta">Última atualização: {{ gerado_em }} &middot; {{ total }} anúncios encontrados com os filtros atuais</div>

  <div class="section-title">🆕 Novos desde a última checagem ({{ novos|length }})</div>
  {% if novos %}
  <div class="grid">
    {% for l in novos %}
    <a class="card-link" href="{{ l.url }}" target="_blank" rel="noopener">
      <div class="card novo">
        {% if l.image_url %}<img src="{{ l.image_url }}" alt="">{% endif %}
        <div class="card-body">
          <span class="badge">novo</span>
          <span class="source">{{ l.source }}{% if l.bairro %} · {{ l.bairro }}{% endif %}</span>
          <span class="title">{{ l.title }}</span>
          <span class="price">{{ l.price_fmt }}</span>
          <span class="details">{{ l.details }}</span>
        </div>
      </div>
    </a>
    {% endfor %}
  </div>
  {% else %}
  <p class="empty">Nenhum anúncio novo desde a última checagem.</p>
  {% endif %}

  <div class="section-title">Todos os anúncios que batem com o filtro ({{ todos|length }})</div>
  <div class="grid">
    {% for l in todos %}
    <a class="card-link" href="{{ l.url }}" target="_blank" rel="noopener">
      <div class="card">
        {% if l.image_url %}<img src="{{ l.image_url }}" alt="">{% endif %}
        <div class="card-body">
          <span class="source">{{ l.source }}{% if l.bairro %} · {{ l.bairro }}{% endif %}</span>
          <span class="title">{{ l.title }}</span>
          <span class="price">{{ l.price_fmt }}</span>
          <span class="details">{{ l.details }}</span>
        </div>
      </div>
    </a>
    {% endfor %}
  </div>
</body>
</html>
"""


def _fmt(listing: Listing):
    price_fmt = (
        f"R$ {listing.price:,.0f}".replace(",", ".") if listing.price else "Preço sob consulta"
    )
    details_parts = []
    if listing.quartos:
        details_parts.append(f"{listing.quartos} quarto(s)")
    if listing.area_m2:
        details_parts.append(f"{listing.area_m2:.0f} m²")
    details = " · ".join(details_parts)
    listing.price_fmt = price_fmt
    listing.details = details
    return listing


def render_html(
    todos: List[Listing],
    novos: List[Listing],
    out_path: str = os.path.join(os.path.dirname(__file__), "..", "docs", "index.html"),
) -> None:
    todos = [_fmt(l) for l in todos]
    novos = [_fmt(l) for l in novos]
    # anúncios novos primeiro dentro de "todos" também, pra facilitar a leitura
    todos.sort(key=lambda l: (l.id not in {n.id for n in novos},))

    template = Template(TEMPLATE)
    html = template.render(
        gerado_em=datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC"),
        total=len(todos),
        todos=todos,
        novos=novos,
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
