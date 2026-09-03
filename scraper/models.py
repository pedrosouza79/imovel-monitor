"""Modelos de dados usados pelo scraper."""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Listing:
    """Representa um anúncio de imóvel normalizado, independente do site de origem."""

    id: str  # identificador único e estável (ex: "wimoveis:3007987622")
    source: str  # "wimoveis" | "dfimoveis" | "61imoveis"
    title: str
    url: str
    price: Optional[float]  # em reais, None se "sob consulta" ou não encontrado
    bairro: Optional[str]
    quartos: Optional[int]
    area_m2: Optional[float]
    image_url: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def matches_filters(self, filtros: dict) -> bool:
        """Aplica os filtros do config.yaml sobre este anúncio."""
        if filtros.get("preco_min") is not None and self.price is not None:
            if self.price < filtros["preco_min"]:
                return False
        if filtros.get("preco_max") is not None and self.price is not None:
            if self.price > filtros["preco_max"]:
                return False
        if filtros.get("quartos_min") is not None and self.quartos is not None:
            if self.quartos < filtros["quartos_min"]:
                return False
        if filtros.get("quartos_max") is not None and self.quartos is not None:
            if self.quartos > filtros["quartos_max"]:
                return False
        if filtros.get("area_min") is not None and self.area_m2 is not None:
            if self.area_m2 < filtros["area_min"]:
                return False
        if filtros.get("area_max") is not None and self.area_m2 is not None:
            if self.area_m2 > filtros["area_max"]:
                return False
        return True
