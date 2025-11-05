"""
Configuración del scraper de Goodreads.

Este módulo contiene la clase ScraperConfig que centraliza todos los parámetros
de configuración del scraper: IDs de listas, páginas a scrapear, delays entre
peticiones, rutas de archivos, y configuración de red. También define los nombres
de las columnas que tendrá el CSV generado.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScraperConfig:
    """Parámetros de configuración para el scraper"""
    
    # Parámetros básicos
    list_id: str = "1.Best_Books_Ever"
    start_page: int = 1
    end_page: int = 50
    download_covers: bool = True
    
    # Delays para no saturar el servidor
    delay_between_pages: int = 15
    delay_between_covers: int = 2
    max_covers_per_page: int = 3
    
    # Configuración de red
    request_timeout: int = 10
    retry_attempts: int = 3
    rate_limit_wait: int = 120  # tiempo de espera si nos bloquean
    
    # Rutas de archivos
    covers_dir: str = "covers"
    output_file: Optional[str] = None
    
    # User agent para las peticiones HTTP
    user_agent: str = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/91.0.4472.124 Safari/537.36'
    )
    
    def __post_init__(self):
        # Si no se especifica archivo de salida, generar uno automáticamente
        if self.output_file is None:
            # Crear carpeta dataset si no existe
            os.makedirs("dataset", exist_ok=True)
            self.output_file = f"dataset/goodreads_{self.list_id.replace('.', '_')}.csv"
    
    @property
    def base_url(self) -> str:
        return f"https://www.goodreads.com/list/show/{self.list_id}"
    
    @property
    def headers(self) -> dict:
        return {'User-Agent': self.user_agent}


# Nombres de las columnas del CSV
CSV_FIELDNAMES = [
    'title',
    'author',
    'avg_rating',
    'ratings_count',
    'page',
    'cover_url',
    'cover_id',
    'book_url',
    'author_url',
    'scraped_at'
]

