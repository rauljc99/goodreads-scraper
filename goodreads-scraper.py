import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import os
import uuid
import random
from urllib.parse import urljoin
import logging
import signal

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoodreadsScraper:
    def __init__(self, delay_between_pages=30, delay_between_covers=2):
        self.session = requests.Session()
        self.delay_between_pages = delay_between_pages
        self.delay_between_covers = delay_between_covers
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        self.session.headers.update(self.headers)
        
        # Crear carpeta para portadas
        self.covers_dir = "book_covers"
        os.makedirs(self.covers_dir, exist_ok=True)
        
        # Contador para límites
        self.cover_download_count = 0
        self.max_covers_per_session = 100

    def download_cover(self, cover_url, book_title):
        """Descarga la portada con mejor resolución y nombre sanitizado"""
        if not cover_url or cover_url == 'N/A' or self.cover_download_count >= self.max_covers_per_session:
            return 'N/A'
        
        try:
            # Sanitizar nombre PRIMERO para verificar si ya existe
            safe_name = re.sub(r'[^\w\s]', '', book_title)
            safe_name = re.sub(r'\s+', '_', safe_name.lower())[:30]
            filename = f"{safe_name}.jpg"
            filepath = os.path.join(self.covers_dir, filename)
            
            # Verificar si ya existe
            if os.path.exists(filepath):
                logger.info(f"📁 Portada ya existe: {book_title[:30]}")
                return filename
            
            time.sleep(random.uniform(self.delay_between_covers, self.delay_between_covers + 2))
            
            # Mejora de la resolución
            high_res_url = cover_url.replace('._SX50_', '').replace('._SY75_', '').replace('._SX98_', '')
            if '_SX' in high_res_url:
                high_res_url = high_res_url.replace('._SX200_', '._SX400_')
            
            # Descargar
            response = self.session.get(high_res_url, timeout=5)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.cover_download_count += 1
            logger.info(f"✅ Portada {self.cover_download_count}/{self.max_covers_per_session}: {book_title[:30]}")
            return filename
            
        except Exception as e:
            logger.warning(f"❌ Error portada {book_title[:30]}: {e}")
            return 'N/A'

    def get_soup(self, url):
        """Obtiene HTML con manejo de errores"""
        try:
            logger.info(f"🌐 Accediendo a: {url}")
            response = self.session.get(url, timeout=10)
            
            # Verificar rate limiting
            if response.status_code == 429:
                logger.warning("🚨 Rate limit detectado! Esperando 2 minutos...")
                time.sleep(120)
                return self.get_soup(url)
            
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"❌ Error en get_soup: {e}")
            return None

    def extract_book_data(self, book_row, download_covers=True):
        """Extrae datos del libro, opcionalmente descarga portadas"""
        try:
            book = {}
            
            # Título
            title_element = book_row.find('a', class_='bookTitle')
            book['title'] = title_element.get_text(strip=True) if title_element else 'N/A'
            book['book_url'] = urljoin('https://www.goodreads.com', title_element['href']) if title_element else 'N/A'
            
            # Autor
            author_element = book_row.find('a', class_='authorName')
            book['author'] = author_element.get_text(strip=True) if author_element else 'N/A'
            book['author_url'] = urljoin('https://www.goodreads.com', author_element['href']) if author_element else 'N/A'
            
            # Rating
            rating_element = book_row.find('span', class_='minirating')
            if rating_element:
                rating_text = rating_element.get_text(strip=True)
                rating_match = re.search(r'(\d+\.\d+)', rating_text)
                book['avg_rating'] = rating_match.group(1) if rating_match else 'N/A'
                
                ratings_match = re.search(r'([\d,]+)\s+ratings', rating_text)
                book['ratings_count'] = ratings_match.group(1).replace(',', '') if ratings_match else 'N/A'
                
                reviews_match = re.search(r'([\d,]+)\s+reviews', rating_text)
                book['reviews_count'] = reviews_match.group(1).replace(',', '') if reviews_match else 'N/A'
            else:
                book['avg_rating'] = 'N/A'
                book['ratings_count'] = 'N/A'
                book['reviews_count'] = 'N/A'
            
            # Score de la lista
            score_element = book_row.find('span', class_='smallText', string=re.compile('score:'))
            if score_element:
                score_text = score_element.get_text(strip=True)
                score_match = re.search(r'score:\s*([\d,]+)', score_text)
                book['list_score'] = score_match.group(1).replace(',', '') if score_match else 'N/A'
            else:
                book['list_score'] = 'N/A'
            
            # Año de publicación
            year_match = re.search(r'\((\d{4})\)', book['title'])
            book['published_year'] = year_match.group(1) if year_match else 'N/A'
            
            # Posición en la lista
            rank_element = book_row.find('td', class_='number')
            book['rank'] = rank_element.get_text(strip=True) if rank_element else 'N/A'
            
            # Portada del libro
            cover_element = book_row.find('img', class_='bookCover')
            book['cover_url'] = cover_element['src'] if cover_element else 'N/A'
            
            # Descargar portada SOLO si no hemos alcanzado el límite
            if download_covers and self.cover_download_count < self.max_covers_per_session:
                book['cover_id'] = self.download_cover(book['cover_url'], book['title'])
            else:
                book['cover_id'] = 'N/A'
            
            # Timestamp y IDs
            book['scraped_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            book['book_id'] = str(uuid.uuid4())
            
            return book
        except Exception as e:
            logger.error(f"Error extrayendo libro: {e}")
            return None

    def scrape_list_page(self, list_url, page_num=1, download_covers=True):
        if page_num == 1:
            url = list_url
        else:
            url = f"{list_url}?page={page_num}"
        
        soup = self.get_soup(url)
        if not soup:
            return [], False
        
        books = []
        try:
            book_table = soup.find('table', class_='tableList')
            if not book_table:
                return [], False
            
            book_rows = book_table.find_all('tr', itemtype='http://schema.org/Book')
            logger.info(f"📄 Página {page_num}: {len(book_rows)} libros")
            
            for row in book_rows:
                book_data = self.extract_book_data(row, download_covers=download_covers)
                if book_data:
                    book_data['page'] = page_num
                    books.append(book_data)
            
            # Verificar siguiente página
            next_link = soup.find('a', class_='next_page')
            has_next = next_link and 'disabled' not in next_link.get('class', [])
            
            return books, has_next
        except Exception as e:
            logger.error(f"Error en página {page_num}: {e}")
            return [], False

def save_to_csv(books_data, filename):
    if not books_data:
        logger.warning("No hay datos para guardar")
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = books_data[0].keys()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(books_data)
    
    logger.info(f"💾 CSV guardado: {filename}")

def main():
    LIST_SHOW = "1.Best_Books_Ever"
    START_PAGE = 30
    END_PAGE = 50
    DOWNLOAD_COVERS = True
    OUTPUT_FILE = f"goodreads_{LIST_SHOW.replace('.', '_')}.csv"
    
    scraper = GoodreadsScraper(
        delay_between_pages=30,
        delay_between_covers=2
    )
    
    books_data = []
    
    def handle_interrupt(sig, frame):
        print(f"\n\n🛑 Interrupción detectada (Ctrl+C)!")
        print("💾 Guardando datos recolectados hasta ahora...")
        
        if books_data:
            save_to_csv(books_data, OUTPUT_FILE)
            books_with_covers = sum(1 for book in books_data if book['cover_id'] != 'N/A')
            
            print(f"\n📊 RESUMEN PARCIAL:")
            print(f"📚 Libros obtenidos: {len(books_data)}")
            print(f"🖼️  Portadas descargadas: {books_with_covers}")
            print(f"📄 Páginas procesadas: {max(book['page'] for book in books_data)}")
            print(f"💾 Archivo CSV: {OUTPUT_FILE}")
            print(f"📁 Carpeta portadas: {scraper.covers_dir}")
        else:
            print("❌ No hay datos para guardar")
        
        exit(0)
    
    signal.signal(signal.SIGINT, handle_interrupt)
    
    try:
        print("🚀 Iniciando scraping... (Presiona Ctrl+C para interrumpir y guardar)")
        
        base_url = f"https://www.goodreads.com/list/show/{LIST_SHOW}"
        current_page = START_PAGE
        has_next_page = True
        
        logger.info(f"🚀 Iniciando scraping de: {LIST_SHOW} (páginas {START_PAGE}-{END_PAGE})")
        if DOWNLOAD_COVERS:
            logger.info(f"🖼️  Descargando portadas (límite: {scraper.max_covers_per_session})")
        
        while has_next_page and current_page <= END_PAGE:
            books, has_next_page = scraper.scrape_list_page(base_url, current_page, download_covers=DOWNLOAD_COVERS)
            
            books_data.extend(books)
            logger.info(f"📦 Datos acumulados: {len(books_data)} libros")
                        
            if has_next_page and current_page < END_PAGE:
                logger.info(f"⏳ Esperando {scraper.delay_between_pages} segundos...")
                time.sleep(scraper.delay_between_pages)
            
            current_page += 1
        
        logger.info(f"✅ Completado. Total: {len(books_data)} libros")
        
        # Guardar resultado final
        if books_data:
            save_to_csv(books_data, OUTPUT_FILE)
            
            books_with_covers = sum(1 for book in books_data if book['cover_id'] != 'N/A')
            
            print(f"\n📊 RESUMEN FINAL:")
            print(f"📚 Libros obtenidos: {len(books_data)}")
            print(f"🖼️  Portadas descargadas: {books_with_covers}")
            print(f"📄 Páginas procesadas: {max(book['page'] for book in books_data)}")
            print(f"💾 Archivo CSV: {OUTPUT_FILE}")
            print(f"📁 Carpeta portadas: {scraper.covers_dir}")
            
        else:
            print("❌ No se obtuvieron datos")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()