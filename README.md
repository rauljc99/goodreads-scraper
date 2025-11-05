# Goodreads Scraper

Un scraper de Python para extraer datos de listas de libros de Goodreads, desarrollado como parte de la Práctica 1 de la asignatura "Tipología y ciclo de vida de los datos" del Máster en Ciencia de Datos de la UOC.

## Características principales

- Extracción completa de datos bibliográficos (títulos, autores, ratings, scores)
- Descarga automática de portadas en alta resolución
- Configuración flexible de páginas (inicio y fin)
- Scraping responsable con delays configurables
- CLI con argumentos personalizables
- Manejo de interrupciones (Ctrl+C) y reanudación
- Evita duplicados automáticamente

## Instalación

```bash
# Clonar repositorio
git clone <repository-url>
cd goodreads-scraper

# Crear entorno virtual (opcional pero recomendado)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Uso básico

```bash
# Prueba rápida (sin portadas, 1 página)
python scraper.py --end-page 1 --no-covers

# Scraping simple (descarga portadas, puede tardar varios minutos por página)
python scraper.py

# Personalizar páginas
python scraper.py --end-page 10

# Sin portadas (más rápido)
python scraper.py --no-covers

# Lista diferente
python scraper.py --list-id "264.Books_That_Everyone_Should_Read_At_Least_Once"

# Delays personalizados
python scraper.py --delay-pages 30 --delay-covers 5 --end-page 20
```

**Nota**: El CSV se guarda automáticamente después de cada página completada. Si ejecutas sin argumentos, el scraper procesa hasta 50 páginas con descarga de portadas (3 por página), lo que puede tardar varias horas. Para ver resultados rápidos, usa `--end-page 1 --no-covers`.

## Argumentos disponibles

| Argumento | Descripción | Por defecto |
|-----------|-------------|-------------|
| `--list-id` | ID de la lista de Goodreads | 1.Best_Books_Ever |
| `--start-page` | Página inicial | 1 |
| `--end-page` | Página final | 50 |
| `--download-covers` | Descargar portadas | True |
| `--no-covers` | Desactivar portadas | False |
| `--max-covers-per-page` | Máximo portadas/página | 3 |
| `--delay-pages` | Segundos entre páginas | 15 |
| `--delay-covers` | Segundos entre portadas | 2 |
| `--output` | Archivo CSV salida | auto |
| `--covers-dir` | Carpeta portadas | covers |
| `--verbose` | Logging detallado | False |

## Estructura del proyecto

```
goodreads-scraper/
├── source/                    # Código fuente
│   ├── config.py              # Configuración
│   ├── scraper.py             # Clase principal
│   ├── parser.py              # Parsing HTML
│   ├── file_handler.py        # Manejo CSV
│   ├── utils.py               # Utilidades
│   └── main.py                # CLI
├── dataset/                   # CSVs generados y portadas
│   └── covers/                # Portadas
├── scraper.py                 # Entrada principal
├── README.md                  # Este documento
└── requirements.txt
```

## Dataset generado

El CSV incluye estas columnas:

| Campo | Descripción |
|-------|-------------|
| title | Título del libro |
| author | Autor |
| avg_rating | Rating promedio (1-5) |
| ratings_count | Número de ratings |
| page | Página donde apareció |
| cover_url | URL original portada |
| cover_id | Archivo portada descargado |
| book_url | URL Goodreads del libro |
| author_url | URL Goodreads del autor |
| scraped_at | Timestamp scraping |

## Uso programático

```python
from source import GoodreadsScraper, ScraperConfig
from source.file_handler import save_to_csv

# Configuración
config = ScraperConfig(
    list_id="1.Best_Books_Ever",
    start_page=1,
    end_page=5,
    download_covers=True
)

# Scraping
scraper = GoodreadsScraper(config)
books = scraper.scrape()

# Guardar
save_to_csv(books, config.output_file)
```

## Listas populares de Goodreads

- `1.Best_Books_Ever` - Mejores libros de todos los tiempos
- `264.Books_That_Everyone_Should_Read_At_Least_Once` - Imprescindibles
- `50.The_Best_Epic_Fantasy` - Mejor fantasía épica
- `2681.Must_Read_Nonfiction` - No ficción esencial

Para más listas: [goodreads.com/list](https://www.goodreads.com/list)

## Scraping responsable

Este scraper implementa buenas prácticas:

- Delays entre peticiones (15s por defecto)
- Límite de portadas por página (3)
- User-Agent identificable
- Manejo de rate limiting (429)
- No redescarga archivos existentes

**Importante**: Uso educativo. Respetar términos de servicio de Goodreads.

## Funcionalidades

### Interrupción segura
Ctrl+C guarda automáticamente el progreso actual y muestra resumen.

### Reanudación inteligente
- No redescarga portadas existentes
- Actualiza portadas faltantes en libros existentes
- Sin duplicados (usa book_url como clave única)

### Optimizaciones
- Búsquedas rápidas con diccionarios
- Procesamiento por páginas

## Troubleshooting

**Módulo no encontrado**
```bash
cd goodreads-scraper
python scraper.py
```

**Dependencias faltantes**
```bash
pip install -r requirements.txt
```

**Rate limiting**  
El script espera automáticamente 2 minutos y reintenta.

**Debug**
```bash
python scraper.py --verbose --end-page 1
```

## DOI Dataset

A publicar en Zenodo.

## Licencia

A decidir.

## Autores

Raúl Javierre y
José Marín

---

**Disclaimer**: Herramienta educativa. Respetar términos de servicio de Goodreads y Amazon.
