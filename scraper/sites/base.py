"""Interface comum que cada scraper de site implementa."""
from abc import ABC, abstractmethod
from typing import List

from ..models import Listing


class SiteScraper(ABC):
    name: str

    @abstractmethod
    def search(self, filtros: dict, paginas: int) -> List[Listing]:
        """Busca anúncios no site de acordo com os filtros e retorna a lista
        de Listing encontrados (ainda sem aplicar o filtro de preço/área/
        quartos — isso é feito depois, de forma centralizada, em
        Listing.matches_filters)."""
        raise NotImplementedError
