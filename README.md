# Goodreads Scraper

Un scraper de Python para extraer datos de listas de libros de Goodreads, desarrollado como parte de la Práctica 1 de la asignatura "Tipología y ciclo de vida de los datos" del Máster en Ciencia de Datos de la UOC.

## Características

- Extracción completa de datos bibliográficos (títulos, autores, ratings, scores)
- Descarga automática de portadas en alta resolución
- Configuración flexible de páginas (inicio y fin)
- Scraping responsable con delays configurables
- Manejo seguro de interrupciones (Ctrl+C)
- Exportación a CSV listo para análisis

## Instalación Rápida

### Prerrequisitos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. Crear entorno virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instalar dependencias
```bash
pip install requests beautifulsoup4
```

## Uso

### Configuración básica
Modificar las variables en la función `main()` del script:

```python
LIST_SHOW = "1.Best_Books_Ever"    # ID de la lista de Goodreads
START_PAGE = 1                      # Página inicial (1-based)
END_PAGE = 5                        # Página final
DOWNLOAD_COVERS = True              # Descargar portadas (True/False)
DELAY_BETWEEN_PAGES = 30            # Segundos entre páginas
DELAY_BETWEEN_COVERS = 2            # Segundos entre descargas de portadas
```

### Ejecución
```bash
python goodreads_scraper.py
```

### Ejemplos de listas populares
- "1.Best_Books_Ever"
- "264.Books_That_Everyone_Should_Read_At_Least_Once"
- "50.The_Best_Epic_Fantasy"
- "2681.Must_Read_Nonfiction"

## Estructura del Dataset

El CSV generado contiene las siguientes columnas:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| title | string | Título del libro |
| author | string | Autor del libro |
| avg_rating | float | Rating promedio (1-5) |
| ratings_count | int | Número total de ratings |
| reviews_count | int | Número total de reseñas |
| list_score | int | Puntuación en la lista |
| published_year | int | Año de publicación |
| rank | int | Posición en la lista |
| page | int | Página donde fue encontrado |
| cover_url | string | URL original de la portada |
| cover_id | string | Nombre del archivo de portada |
| book_url | string | URL del libro en Goodreads |
| author_url | string | URL del autor en Goodreads |
| book_id | string | ID único del libro |
| scraped_at | datetime | Fecha y hora del scraping |

## Estructura del Proyecto

```
goodreads-scraper/
├── goodreads_scraper.py     # Script principal
├── requirements.txt         # Dependencias de Python
├── book_covers/            # Carpeta de portadas descargadas
│   ├── titulo_libro1.jpg
│   ├── titulo_libro2.jpg
│   └── ...
├── goodreads_1_Best_Books_Ever.csv  # Dataset generado
└── README.md               # Este archivo
```

## Consideraciones Éticas

Este scraper incluye medidas para el scraping responsable:

- Delays configurables entre peticiones
- Límites en descargas de portadas (10 por ejecución)
- User-Agent identificable
- Manejo automático de rate limiting
- Verificación de existencia de archivos para evitar duplicados

**Nota importante**: Este proyecto es para fines educativos. Los datos pertenecen a Goodreads y deben usarse respetando sus términos de servicio.

## Funcionalidades Avanzadas

### Interrupción Segura
Presiona `Ctrl+C` en cualquier momento para:
- Guardar automáticamente los datos recolectados
- Mostrar resumen parcial
- Salir limpiamente del programa

### Reanudación Inteligente
- Las portadas no se redescargan si ya existen
- Puedes ejecutar múltiples veces incrementando el rango de páginas

## Solución de Problemas

### Errores comunes:
1. **Dependencias faltantes**: Ejecutar `pip install -r requirements.txt`
2. **Lista no encontrada**: Verificar que el ID de lista existe
3. **Rate limiting**: El script espera automáticamente 2 minutos
4. **Portadas no descargan**: Revisar conexión a internet y límites

### Logs detallados
El script proporciona logs informativos sobre:
- Progreso del scraping
- Errores específicos
- Estadísticas de descargas
- Tiempos de espera

## Licencia

Este proyecto está bajo la Licencia MIT.

---

**Desarrollado para la Práctica 1 de Tipología y ciclo de vida de los datos - UOC**