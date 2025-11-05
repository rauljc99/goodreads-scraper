"""
Paquete principal del scraper de Goodreads.

"""

from .scraper import GoodreadsScraper
from .config import ScraperConfig

__all__ = ["GoodreadsScraper", "ScraperConfig"]

