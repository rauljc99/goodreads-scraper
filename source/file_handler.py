"""
Manejo de archivos CSV y portadas.

Este módulo se encarga de todas las operaciones con archivos: cargar datos existentes
del CSV, guardar nuevos datos, y combinar datos nuevos con existentes evitando
duplicados. También incluye funciones auxiliares para verificar existencia de archivos
y crear directorios.
"""

import os
import csv
import logging
from typing import List, Dict

from .config import CSV_FIELDNAMES

logger = logging.getLogger(__name__)


def get_max_page_scraped(existing_books: List[Dict[str, str]]) -> int:
    """Obtiene la página más alta que ya fue scrapeada"""
    if not existing_books:
        return 0
    
    max_page = 0
    for book in existing_books:
        try:
            page_num = int(book.get('page', 0))
            if page_num > max_page:
                max_page = page_num
        except (ValueError, TypeError):
            continue
    
    return max_page


def load_existing_data(filename: str) -> List[Dict[str, str]]:
    """Carga datos existentes del CSV si existe"""
    existing_books = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                existing_books = list(reader)
            logger.info(f"Cargados {len(existing_books)} libros existentes de {filename}")
        except Exception as e:
            logger.warning(f"Error cargando archivo existente: {e}")
    return existing_books


def get_existing_book_map(existing_books: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """Crea un diccionario para búsquedas rápidas por URL"""
    return {
        book['book_url']: book
        for book in existing_books
        if book.get('book_url') != 'N/A'
    }


def merge_books_data(
    existing_books: List[Dict[str, str]],
    new_books: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """
    Combina libros existentes con nuevos, evitando duplicados.
    """
    existing_book_map = get_existing_book_map(existing_books)
    new_books_count = 0
    updated_covers = 0
    
    # Copiar el mapa existente
    merged_map = existing_book_map.copy()
    
    for new_book in new_books:
        book_url = new_book['book_url']
        
        if book_url in merged_map:
            # Libro ya existe - actualizar portada si hace falta
            existing_book = merged_map[book_url]
            if existing_book.get('cover_id') == 'N/A' and new_book.get('cover_id') != 'N/A':
                existing_book['cover_id'] = new_book['cover_id']
                updated_covers += 1
        else:
            # Libro nuevo - añadir
            merged_map[book_url] = new_book
            new_books_count += 1
    
    # Convertir de vuelta a lista
    merged_books = list(merged_map.values())
    
    logger.info(
        f"Merge: {len(existing_books)} existentes + "
        f"{new_books_count} nuevos + {updated_covers} portadas actualizadas"
    )
    
    return merged_books


def save_to_csv(books_data: List[Dict[str, str]], filename: str) -> None:
    """Guarda los datos en un archivo CSV"""
    if not books_data:
        logger.warning("No hay datos para guardar")
        return
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = CSV_FIELDNAMES if CSV_FIELDNAMES else books_data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(books_data)
        
        logger.info(f"CSV guardado: {filename} ({len(books_data)} libros)")
    except Exception as e:
        logger.error(f"Error al guardar CSV: {e}")


def ensure_directory_exists(directory: str) -> None:
    """Crea el directorio si no existe"""
    os.makedirs(directory, exist_ok=True)


def file_exists(filepath: str) -> bool:
    """Verifica si un archivo existe"""
    return os.path.exists(filepath)

