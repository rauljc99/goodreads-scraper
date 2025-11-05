"""
Funciones para parsear el HTML y extraer datos de libros.

Este módulo contiene toda la lógica de extracción de datos del HTML de Goodreads.
Incluye funciones para encontrar libros en una página, extraer información de cada
libro (título, autor, rating, URLs), verificar si hay páginas siguientes, y mejorar
la resolución de las URLs de las portadas para obtener imágenes más grandes.
"""

import time
import logging
from typing import Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag

from .utils import extract_number, extract_ratings_count

logger = logging.getLogger(__name__)


def extract_book_data(book_row: Tag, page_num: int) -> Optional[Dict[str, str]]:
    """Extrae toda la información de un libro de una fila de la tabla"""
    try:
        book = {}
        
        # Título del libro
        title_element = book_row.find('a', class_='bookTitle')
        book['title'] = title_element.get_text(strip=True) if title_element else 'N/A'
        book['book_url'] = (
            urljoin('https://www.goodreads.com', title_element['href'])
            if title_element and title_element.get('href')
            else 'N/A'
        )
        
        # Autor
        author_element = book_row.find('a', class_='authorName')
        book['author'] = author_element.get_text(strip=True) if author_element else 'N/A'
        book['author_url'] = (
            urljoin('https://www.goodreads.com', author_element['href'])
            if author_element and author_element.get('href')
            else 'N/A'
        )
        
        # Rating promedio y número de ratings
        rating_element = book_row.find('span', class_='minirating')
        if rating_element:
            rating_text = rating_element.get_text(strip=True)
            book['avg_rating'] = extract_number(rating_text) or 'N/A'
            book['ratings_count'] = extract_ratings_count(rating_text) or 'N/A'
        else:
            book['avg_rating'] = 'N/A'
            book['ratings_count'] = 'N/A'
        
        # URL de la portada
        cover_element = book_row.find('img', class_='bookCover')
        book['cover_url'] = cover_element['src'] if cover_element and cover_element.get('src') else 'N/A'
        
        # Metadata adicional
        book['cover_id'] = 'N/A'  # se actualizará si se descarga la portada
        book['page'] = str(page_num)
        book['scraped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return book
        
    except Exception as e:
        logger.error(f"Error extrayendo datos del libro: {e}")
        return None


def find_books_in_page(soup: BeautifulSoup) -> list:
    """Encuentra todos los libros en la página"""
    book_table = soup.find('table', class_='tableList')
    if not book_table:
        return []
    
    return book_table.find_all('tr', itemtype='http://schema.org/Book')


def has_next_page(soup: BeautifulSoup) -> bool:
    """Verifica si hay una página siguiente"""
    next_link = soup.find('a', class_='next_page')
    return next_link and 'disabled' not in next_link.get('class', [])


def improve_cover_resolution(cover_url: str) -> str:
    """Mejora la resolución de la URL de la portada (truco para obtener imágenes más grandes)"""
    if not cover_url or cover_url == 'N/A':
        return cover_url
    
    # Quitar marcadores de baja resolución
    high_res_url = cover_url.replace('._SX50_', '').replace('._SY75_', '').replace('._SX98_', '')
    
    # Subir a resolución mayor
    if '_SX' in high_res_url:
        high_res_url = high_res_url.replace('._SX200_', '._SX400_')
    
    return high_res_url

