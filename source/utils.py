"""
Funciones auxiliares para el scraper.

Este módulo proporciona utilidades compartidas: configuración de logging,
sanitización de nombres de archivo para evitar caracteres problemáticos,
y funciones para extraer números y conteos de ratings usando expresiones
regulares. Son funciones simples pero reutilizables en varios módulos.
"""

import re
import logging
from typing import Optional


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configura el logging del scraper"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def sanitize_filename(text: str, max_length: int = 30) -> str:
    """
    Limpia el texto para usarlo como nombre de archivo
    Ej: "Harry Potter and the..." -> "harry_potter_and_the"
    """
    safe_name = re.sub(r'[^\w\s]', '', text)  # quitar caracteres raros
    safe_name = re.sub(r'\s+', '_', safe_name.lower())  # espacios -> _
    return safe_name[:max_length]


def extract_number(text: str) -> Optional[str]:
    """Extrae el primer número decimal del texto (ej: "4.23 avg rating" -> "4.23")"""
    match = re.search(r'(\d+\.\d+)', text)
    return match.group(1) if match else None


def extract_ratings_count(text: str) -> Optional[str]:
    """Extrae el número de ratings (ej: "1,234 ratings" -> "1234")"""
    match = re.search(r'([\d,]+)\s+ratings', text)
    return match.group(1).replace(',', '') if match else None

