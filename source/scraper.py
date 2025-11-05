"""
Clase principal del scraper de Goodreads.

Este módulo contiene la clase GoodreadsScraper que es el núcleo del scraper.
Se encarga de hacer las peticiones HTTP a Goodreads, descargar portadas de libros,
manejar rate limiting y timeouts, y orquestar el proceso completo de scraping
de múltiples páginas. Usa una sesión de requests para mantener cookies y headers
entre peticiones.
"""

import os
import time
import random
import logging
from typing import List, Dict, Tuple, Optional
import requests
from bs4 import BeautifulSoup

from .config import ScraperConfig
from .parser import (
    extract_book_data,
    find_books_in_page,
    has_next_page,
    improve_cover_resolution
)
from .file_handler import ensure_directory_exists, file_exists
from .utils import sanitize_filename

logger = logging.getLogger(__name__)


class GoodreadsScraper:
    """Scraper para extraer datos de listas de Goodreads"""
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)
        
        # Crear carpeta para las portadas
        ensure_directory_exists(config.covers_dir)
        
        # Contador de portadas descargadas en la página actual
        self.cover_download_count = 0
    
    def download_cover(self, cover_url: str, book_title: str) -> str:
        """Descarga la portada de un libro"""
        # Verificar límites
        if (not cover_url or 
            cover_url == 'N/A' or 
            self.cover_download_count >= self.config.max_covers_per_page):
            return 'N/A'
        
        try:
            # Generar nombre de archivo seguro
            safe_name = sanitize_filename(book_title)
            filename = f"{safe_name}.jpg"
            filepath = os.path.join(self.config.covers_dir, filename)
            
            # Si ya existe, no descargar de nuevo
            if file_exists(filepath):
                logger.info(f"Portada ya existe: {book_title[:30]}")
                return filename
            
            # Delay para no saturar el servidor
            time.sleep(random.uniform(
                self.config.delay_between_covers,
                self.config.delay_between_covers + 2
            ))
            
            # Mejorar resolución de la URL
            high_res_url = improve_cover_resolution(cover_url)
            
            # Descargar imagen
            response = self.session.get(high_res_url, timeout=5)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.cover_download_count += 1
            logger.info(
                f"Portada {self.cover_download_count}/"
                f"{self.config.max_covers_per_page}: {book_title[:30]}"
            )
            return filename
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error descargando portada {book_title[:30]}: {e}")
            return 'N/A'
        except Exception as e:
            logger.warning(f"Error inesperado con portada {book_title[:30]}: {e}")
            return 'N/A'
    
    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Obtiene el HTML de la URL y devuelve un objeto BeautifulSoup"""
        try:
            logger.info(f"Accediendo a: {url}")
            response = self.session.get(url, timeout=self.config.request_timeout)
            
            # Manejar rate limiting (error 429)
            if response.status_code == 429:
                logger.warning(
                    f"Rate limit detectado! Esperando {self.config.rate_limit_wait} segundos..."
                )
                time.sleep(self.config.rate_limit_wait)
                return self.get_soup(url)  # reintentar
            
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout al acceder: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de petición: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return None
    
    def scrape_list_page(
        self,
        page_num: int,
        download_covers: bool = True
    ) -> Tuple[List[Dict[str, str]], bool]:
        """Scrapea una página de la lista y devuelve los libros encontrados"""
        # Resetear contador de portadas
        self.cover_download_count = 0
        
        # Construir URL
        if page_num == 1:
            url = self.config.base_url
        else:
            url = f"{self.config.base_url}?page={page_num}"
        
        # Obtener contenido HTML
        soup = self.get_soup(url)
        if not soup:
            return [], False
        
        books = []
        try:
            # Encontrar todos los libros en la página
            book_rows = find_books_in_page(soup)
            logger.info(f"Página {page_num}: {len(book_rows)} libros")
            
            # Extraer datos de cada libro
            for row in book_rows:
                book_data = extract_book_data(row, page_num)
                if book_data:
                    # Descargar portada si está habilitado y no hemos llegado al límite
                    if (download_covers and 
                        self.cover_download_count < self.config.max_covers_per_page):
                        cover_id = self.download_cover(
                            book_data['cover_url'],
                            book_data['title']
                        )
                        book_data['cover_id'] = cover_id
                    
                    books.append(book_data)
            
            # Verificar si hay página siguiente
            has_next = has_next_page(soup)
            
            return books, has_next
            
        except Exception as e:
            logger.error(f"Error en página {page_num}: {e}")
            return [], False
    
    def scrape(
        self,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
        download_covers: Optional[bool] = None
    ) -> List[Dict[str, str]]:
        """Scrapea múltiples páginas y devuelve todos los libros"""
        start = start_page or self.config.start_page
        end = end_page or self.config.end_page
        download = download_covers if download_covers is not None else self.config.download_covers
        
        all_books = []
        current_page = start
        has_next_page_flag = True
        
        logger.info(
            f"Iniciando scraping: {self.config.list_id} "
            f"(páginas {start}-{end})"
        )
        
        if download:
            logger.info(f"Descargando portadas (límite: {self.config.max_covers_per_page}/página)")
        
        while has_next_page_flag and current_page <= end:
            books, has_next_page_flag = self.scrape_list_page(
                current_page,
                download_covers=download
            )
            
            all_books.extend(books)
            logger.info(
                f"Página {current_page} completada: {len(books)} libros "
                f"(Total: {len(all_books)})"
            )
            
            # Esperar antes de la siguiente página
            if has_next_page_flag and current_page < end:
                logger.info(f"Esperando {self.config.delay_between_pages} segundos...")
                time.sleep(self.config.delay_between_pages)
            
            current_page += 1
        
        logger.info(f"Scraping completado. Total: {len(all_books)} libros")
        return all_books

