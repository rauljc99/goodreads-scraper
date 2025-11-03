"""
Entrypoint principal del scraper (con CLI).

Este módulo es el punto de entrada cuando se ejecuta el scraper desde la línea de
comandos. Contiene la función main() que parsea argumentos con argparse, configura
el logging, crea el scraper y ejecuta el proceso completo. También maneja las
interrupciones (Ctrl+C) para guardar los datos de forma segura antes de salir.
Incluye funciones para mostrar resúmenes y crear la configuración desde argumentos CLI.
"""

import sys
import signal
import argparse
import logging
import time
from typing import List, Dict, Optional

from .config import ScraperConfig
from .scraper import GoodreadsScraper
from .file_handler import load_existing_data, merge_books_data, save_to_csv, get_max_page_scraped
from .utils import setup_logging

logger = logging.getLogger(__name__)

# Variables globales para el handler de Ctrl+C
books_data: List[Dict[str, str]] = []
existing_books: List[Dict[str, str]] = []
config: Optional[ScraperConfig] = None


def handle_interrupt(sig, frame):  # pylint: disable=unused-argument
    """Maneja Ctrl+C y guarda los datos antes de salir"""
    print("\n\nInterrupción detectada (Ctrl+C)!")
    print("Guardando datos recolectados...")
    
    if books_data and config:
        save_to_csv(books_data, config.output_file)
        books_with_covers = sum(1 for book in books_data if book.get('cover_id') != 'N/A')
        
        print("\nRESUMEN PARCIAL:")
        print(f"Total de libros: {len(books_data)}")
        print(f"Libros nuevos añadidos: {len(books_data) - len(existing_books)}")
        print(f"Portadas descargadas: {books_with_covers}")
        if books_data:
            max_page = max(int(book.get('page', 0)) for book in books_data)
            print(f"Páginas procesadas: {max_page}")
        print(f"Archivo CSV: {config.output_file}")
        print(f"Carpeta de portadas: {config.covers_dir}")
    else:
        print("No hay datos para guardar")
    
    sys.exit(0)


def parse_arguments() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Scrape book data from Goodreads lists',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Argumentos básicos
    parser.add_argument('--list-id', type=str, default='1.Best_Books_Ever',
                       help='ID de la lista de Goodreads')
    parser.add_argument('--start-page', type=int, default=1,
                       help='Página inicial')
    parser.add_argument('--end-page', type=int, default=50,
                       help='Página final')
    
    # Portadas
    parser.add_argument('--download-covers', action='store_true', default=True,
                       help='Descargar portadas')
    parser.add_argument('--no-covers', action='store_true',
                       help='Desactivar descarga de portadas')
    parser.add_argument('--max-covers-per-page', type=int, default=3,
                       help='Máximo de portadas por página')
    
    # Delays
    parser.add_argument('--delay-pages', type=int, default=15,
                       help='Segundos entre páginas')
    parser.add_argument('--delay-covers', type=int, default=2,
                       help='Segundos entre descargas de portadas')
    
    # Archivos
    parser.add_argument('--output', type=str,
                       help='Nombre del archivo CSV de salida')
    parser.add_argument('--covers-dir', type=str, default='covers',
                       help='Carpeta para guardar portadas')
    
    # Logging
    parser.add_argument('--verbose', action='store_true',
                       help='Logging detallado')
    parser.add_argument('--quiet', action='store_true',
                       help='Logging mínimo')
    
    return parser.parse_args()


def create_config_from_args(args: argparse.Namespace) -> ScraperConfig:
    """Crea la configuración a partir de los argumentos"""
    download_covers = args.download_covers and not args.no_covers
    
    return ScraperConfig(
        list_id=args.list_id,
        start_page=args.start_page,
        end_page=args.end_page,
        download_covers=download_covers,
        delay_between_pages=args.delay_pages,
        delay_between_covers=args.delay_covers,
        max_covers_per_page=args.max_covers_per_page,
        covers_dir=args.covers_dir,
        output_file=args.output
    )


def print_summary(all_books: List[Dict[str, str]], prev_books: List[Dict[str, str]], scraper_config: ScraperConfig):
    """Muestra el resumen final del scraping"""
    books_with_covers = sum(1 for book in all_books if book.get('cover_id') != 'N/A')
    new_books_count = len(all_books) - len(prev_books)
    
    print("\nRESUMEN FINAL:")
    print(f"Total de libros: {len(all_books)}")
    print(f"Libros nuevos añadidos: {new_books_count}")
    print(f"Portadas descargadas: {books_with_covers}")
    
    if all_books:
        max_page = max(int(book.get('page', 0)) for book in all_books)
        print(f"Páginas procesadas: {max_page}")
    
    print(f"Archivo CSV: {scraper_config.output_file}")
    print(f"Carpeta de portadas: {scraper_config.covers_dir}")


def main():
    """Función principal"""
    global books_data, existing_books, config
    
    # Parsear argumentos
    args = parse_arguments()
    
    # Configurar logging
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    
    setup_logging(log_level)
    
    # Crear configuración
    config = create_config_from_args(args)
    
    # Configurar handler para Ctrl+C
    signal.signal(signal.SIGINT, handle_interrupt)
    
    try:
        print("Iniciando scraping... (Presiona Ctrl+C para interrumpir y guardar)")
        
        # Cargar datos existentes
        existing_books = load_existing_data(config.output_file)
        books_data = existing_books.copy()
        
        logger.info(f"Base de datos existente: {len(existing_books)} libros")
        
        # Ajustar página inicial si hay datos existentes
        if existing_books:
            max_page_scraped = get_max_page_scraped(existing_books)
            if max_page_scraped > 0 and config.start_page <= max_page_scraped:
                # Continuar desde la siguiente página
                new_start_page = max_page_scraped + 1
                logger.info(f"Última página scrapeada: {max_page_scraped}. Continuando desde página {new_start_page}")
                config.start_page = new_start_page
        
        # Crear scraper
        scraper = GoodreadsScraper(config)
        
        # Scrapear página por página y guardar después de cada una
        start = config.start_page
        end = config.end_page
        download = config.download_covers
        
        current_page = start
        has_next_page_flag = True
        total_new_books = 0
        
        logger.info(
            f"Iniciando scraping: {config.list_id} "
            f"(páginas {start}-{end})"
        )
        
        if download:
            logger.info(f"Descargando portadas (límite: {config.max_covers_per_page}/página)")
        
        while has_next_page_flag and current_page <= end:
            try:
                # Scrapear una página
                page_books, has_next_page_flag = scraper.scrape_list_page(
                    current_page,
                    download_covers=download
                )
                
                logger.info(f"Scrapeada página {current_page}: {len(page_books)} libros obtenidos")
                
                if page_books:
                    # Combinar con datos existentes
                    books_data = merge_books_data(books_data, page_books)
                    
                    # Guardar después de cada página para no perder datos
                    try:
                        save_to_csv(books_data, config.output_file)
                        total_new_books += len(page_books)
                        logger.info(
                            f"Página {current_page} guardada: {len(page_books)} libros nuevos "
                            f"(Total en CSV: {len(books_data)})"
                        )
                    except Exception as save_error:
                        logger.error(f"Error al guardar página {current_page}: {save_error}")
                        # Intentar guardar de nuevo en el handler de interrupción
                        raise
                else:
                    logger.warning(f"No se obtuvieron libros en la página {current_page}")
                
                # Esperar antes de la siguiente página
                if has_next_page_flag and current_page < end:
                    logger.info(f"Esperando {config.delay_between_pages} segundos...")
                    time.sleep(config.delay_between_pages)
                
                current_page += 1
                
            except KeyboardInterrupt:
                # Re-lanzar para que el handler lo capture
                raise
            except Exception as page_error:
                logger.error(f"Error procesando página {current_page}: {page_error}")
                # Intentar guardar lo que tengamos hasta ahora
                if books_data:
                    try:
                        save_to_csv(books_data, config.output_file)
                        logger.info(f"Datos guardados después del error en página {current_page}")
                    except Exception:
                        pass
                current_page += 1
                continue
        
        # Resumen final
        if books_data:
            print_summary(books_data, existing_books, config)
        else:
            print("No se obtuvieron datos")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

