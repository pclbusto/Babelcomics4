# Filtros y Búsqueda

El sistema de filtros y búsqueda de Babelcomics4 proporciona herramientas potentes para encontrar comics específicos en tu colección, utilizando múltiples criterios y combinaciones avanzadas.

## 🔍 Búsqueda Básica

### Barra de Búsqueda Principal
```
┌─────────────────────────────────────────────────┐
│ 🔍 [Buscar en tu colección...]            [🔎] │
└─────────────────────────────────────────────────┘
```

La búsqueda básica es **instantánea** y busca en tiempo real mientras escribes.

### Campos de Búsqueda

#### Información del Archivo
```bash
# Nombre del archivo
superman.cbz
batman_001
walking_dead

# Ruta completa del archivo
/Comics/DC/Batman/
/home/user/Comics/Marvel/

# Extensión de archivo
.cbz
.cbr
.pdf
```

#### Metadata Catalogada
```bash
# Título del comic
"The Amazing Spider-Man"
"Batman Rebirth"
"Watchmen"

# Editorial
"DC Comics"
"Marvel Comics"
"Image Comics"

# Nombre del volumen
"Batman (2016)"
"Spider-Man (2018)"
"The Walking Dead (2003)"

# Descripción/Resumen
"dark knight"
"web slinger"
"zombie apocalypse"
```

### Ejemplos de Búsqueda

#### Búsquedas Simples
```
Batman          → Todos los comics con "Batman"
Spider-Man #1   → Issue #1 de cualquier Spider-Man
2018           → Comics del año 2018
DC Comics      → Todos los comics de DC
rebirth        → Comics relacionados con "Rebirth"
```

#### Búsquedas por Archivo
```
.cbz           → Solo archivos CBZ
batman_001     → Archivo específico
/DC/           → Comics en directorio DC
45.2 MB        → Por tamaño de archivo
```

## 🎛️ Filtros Avanzados

### Panel de Filtros
```
┌─── Filtros Avanzados ─────────────────────────┐
│                                               │
│ 📊 Clasificación:                            │
│ ○ Todos los comics                           │
│ ○ Solo clasificados                          │
│ ○ Solo sin clasificar                        │
│                                               │
│ ⭐ Calidad:                                  │
│ Mínima: [⭐] ────○──── [⭐⭐⭐⭐⭐]         │
│ Máxima: [⭐] ──────────○ [⭐⭐⭐⭐⭐]       │
│                                               │
│ 🏢 Editorial:                                │
│ ☑️ DC Comics         ☑️ Marvel Comics        │
│ ☐ Image Comics      ☐ Dark Horse            │
│ ☐ IDW Publishing    ☐ Otras                  │
│                                               │
│ 📅 Rango de Años:                           │
│ Desde: [2010] Hasta: [2024]                  │
│                                               │
│ 📁 Estado de Archivo:                        │
│ ☑️ Archivos existentes                       │
│ ☐ Incluir elementos en papelera             │
│ ☐ Solo archivos corruptos                   │
│                                               │
│ 💾 Tamaño de Archivo:                        │
│ Mín: [10] MB  Máx: [200] MB                  │
│                                               │
│ [🔄 Aplicar] [❌ Limpiar] [💾 Guardar]      │
└───────────────────────────────────────────────┘
```

### Filtros de Clasificación

#### Todos los Comics
- Muestra **toda la colección**
- Incluye clasificados y sin clasificar
- Vista completa de la biblioteca

#### Solo Clasificados
```
Criterios:
✅ Tienen metadata de ComicVine
✅ Título, editorial y volumen definidos
✅ Thumbnail en color
✅ Información completa disponible

Visualización:
🖼️ [Thumbnail Color]
📖 Superman #1 - The Man of Steel
📁 DC Comics | Superman (2018)
⭐⭐⭐⭐⭐ | 📅 2018-07-04
```

#### Solo Sin Clasificar
```
Criterios:
❌ Sin metadata de ComicVine
❌ Solo información del archivo
❌ Thumbnail en escala de grises
❌ Pendiente de catalogación

Visualización:
🖼️ [Thumbnail Gris]
📁 superman_001_unknown.cbz
💾 45.2 MB | 📅 2024-03-15
⭐ Sin calificar | 🏷️ Sin catalogar
```

### Filtros de Calidad

#### Sistema de Calidad por Estrellas
```
⭐     = 1 estrella  - Calidad muy baja
⭐⭐   = 2 estrellas - Calidad baja
⭐⭐⭐ = 3 estrellas - Calidad media
⭐⭐⭐⭐ = 4 estrellas - Calidad buena
⭐⭐⭐⭐⭐ = 5 estrellas - Calidad excelente
```

#### Configuración de Rangos
```python
# Ejemplo: Solo comics de alta calidad
quality_filter = {
    'min_quality': 4,  # ⭐⭐⭐⭐
    'max_quality': 5   # ⭐⭐⭐⭐⭐
}

# Ejemplo: Identificar comics de baja calidad para mejora
quality_filter = {
    'min_quality': 1,  # ⭐
    'max_quality': 2   # ⭐⭐
}
```

### Filtros por Editorial

#### Editoriales Principales
```
🦇 DC Comics
├── Batman, Superman, Wonder Woman
├── Justice League, Teen Titans
└── Watchmen, Sandman, Vertigo

🕷️ Marvel Comics
├── Spider-Man, X-Men, Avengers
├── Fantastic Four, Daredevil
└── Ultimate, Marvel MAX

🌟 Image Comics
├── The Walking Dead, Saga
├── Invincible, Spawn
└── Titles independientes

🐴 Dark Horse Comics
├── Hellboy, Sin City
├── Star Wars (legado)
└── Comics licenciados

📚 Otras Editoriales
├── IDW Publishing
├── Boom! Studios
├── Dynamite Entertainment
└── Editoriales independientes
```

#### Selección Múltiple
```python
# Filtrar múltiples editoriales
editorial_filter = [
    'DC Comics',
    'Marvel Comics',
    'Image Comics'
]

# Excluir editoriales específicas
exclude_publishers = [
    'Publisher Unknown',
    'Sin Editorial'
]
```

### Filtros Temporales

#### Por Año de Publicación
```
┌─── Filtro por Año ────────────────────────────┐
│                                               │
│ 📅 Año de Tapa:                              │
│ Desde: [2010] ─────────────── Hasta: [2024]  │
│                                               │
│ 🎯 Presets Rápidos:                          │
│ [2020s] [2010s] [2000s] [1990s] [Clásicos]   │
│                                               │
│ 📊 Distribución por Década:                  │
│ 2020-2024: ████████ 234 comics (22.3%)      │
│ 2010-2019: ██████████ 445 comics (42.4%)    │
│ 2000-2009: ████ 189 comics (18.0%)          │
│ 1990-1999: ██ 98 comics (9.3%)              │
│ Anteriores: ██ 84 comics (8.0%)              │
└───────────────────────────────────────────────┘
```

#### Filtros de Fecha Especiales
```bash
# Comics de la Era Moderna (1985+)
year_range: [1985, 2024]

# Comics de la Era de Plata (1956-1970)
year_range: [1956, 1970]

# Comics de la Era de Oro (1938-1956)
year_range: [1938, 1956]

# Solo comics actuales (últimos 2 años)
year_range: [2022, 2024]

# Comics clásicos (antes de 2000)
year_range: [1938, 1999]
```

### Filtros de Estado de Archivo

#### Estados Disponibles
```
✅ Archivos Existentes
├── Archivo presente en disco
├── Accesible y legible
└── Thumbnail generado

🗑️ En Papelera
├── Marcado como eliminado
├── Oculto en vista normal
└── Recuperable

💔 Archivos Corruptos
├── No se puede abrir
├── Formato inválido
└── Requiere atención

🔗 Enlaces Rotos
├── Archivo movido/eliminado
├── Ruta incorrecta
└── Requiere reubicación
```

#### Casos de Uso
```python
# Solo mostrar archivos válidos (vista normal)
file_status_filter = {
    'include_existing': True,
    'include_trash': False,
    'include_corrupted': False
}

# Gestión de papelera
trash_management_filter = {
    'include_existing': False,
    'include_trash': True,
    'include_corrupted': False
}

# Mantenimiento de colección
maintenance_filter = {
    'include_existing': True,
    'include_trash': True,
    'include_corrupted': True
}
```

## 🔧 Filtros Especializados

### Filtros de Volumen

#### Completitud de Colección
```
┌─── Filtros de Volumen ────────────────────────┐
│                                               │
│ 📊 Completitud de Volumen:                   │
│ ○ Volúmenes completos (100%)                 │
│ ○ Casi completos (80-99%)                    │
│ ○ En progreso (20-79%)                       │
│ ○ Iniciados (1-19%)                          │
│ ○ Sin issues (0%)                            │
│                                               │
│ 📚 Tipo de Volumen:                          │
│ ☑️ Series regulares                          │
│ ☑️ Mini-series                               │
│ ☐ One-shots                                  │
│ ☐ Graphic novels                             │
│ ☐ Trade paperbacks                           │
│                                               │
│ 📅 Estado del Volumen:                       │
│ ☑️ En publicación                            │
│ ☑️ Finalizados                               │
│ ☐ Cancelados                                 │
│ ☐ En pausa                                   │
└───────────────────────────────────────────────┘
```

### Filtros de Tamaño de Archivo

#### Rangos de Tamaño
```python
# Archivos pequeños (comics web/digital)
size_filter = {
    'min_size_mb': 0,
    'max_size_mb': 30
}

# Archivos medianos (calidad estándar)
size_filter = {
    'min_size_mb': 30,
    'max_size_mb': 80
}

# Archivos grandes (alta calidad/resolución)
size_filter = {
    'min_size_mb': 80,
    'max_size_mb': 200
}

# Archivos muy grandes (ultra-alta calidad)
size_filter = {
    'min_size_mb': 200,
    'max_size_mb': 1000
}
```

#### Análisis de Tamaño
```
┌─── Distribución por Tamaño ───────────────────┐
│                                               │
│ 📊 Análisis de Tamaños de Archivo:           │
│                                               │
│ 0-30 MB:   ████ 234 archivos (22.3%)         │
│ 30-50 MB:  ████████ 445 archivos (42.4%)     │
│ 50-80 MB:  ████ 189 archivos (18.0%)         │
│ 80-150 MB: ██ 98 archivos (9.3%)             │
│ 150+ MB:   ██ 84 archivos (8.0%)             │
│                                               │
│ 📈 Tamaño Promedio: 52.4 MB                  │
│ 📊 Tamaño Total: 54.8 GB                     │
│ 🎯 Calidad vs Tamaño: Correlación 0.78       │
└───────────────────────────────────────────────┘
```

## 🔍 Búsqueda Avanzada

### Operadores de Búsqueda

#### Operadores Básicos
```bash
# Búsqueda exacta
"Batman Rebirth"     → Frase exacta
batman AND rebirth   → Ambos términos presentes
batman OR superman   → Cualquiera de los términos
batman NOT year:2016 → Batman excluyendo 2016
```

#### Operadores de Campo
```bash
# Búsqueda por campo específico
title:"The Amazing Spider-Man"
publisher:"DC Comics"
year:2018
quality:5
volume:"Batman (2016)"
issue:1
file:batman_001.cbz
```

#### Operadores de Rango
```bash
# Rangos numéricos
year:2010..2020      → Años entre 2010 y 2020
quality:4..5         → Calidad 4 o 5 estrellas
size:50..100         → Tamaño entre 50-100 MB
issue:1..12          → Issues del 1 al 12
```

#### Comodines
```bash
# Wildcards
batman*              → Comienza con "batman"
*man                 → Termina con "man"
*spider*             → Contiene "spider"
bat?man              → ? representa un carácter
```

### Búsquedas Predefinidas

#### Consultas Rápidas
```
┌─── Búsquedas Predefinidas ────────────────────┐
│                                               │
│ 🔍 Consultas Populares:                      │
│ [🆕 Agregados Recientemente]                  │
│ [⭐ Alta Calidad (4-5 ⭐)]                   │
│ [❌ Sin Catalogar]                           │
│ [🔍 Issues Faltantes]                        │
│ [🗑️ En Papelera]                            │
│                                               │
│ 📚 Por Editorial:                            │
│ [🦇 DC Comics]     [🕷️ Marvel Comics]        │
│ [🌟 Image Comics]  [🐴 Dark Horse]           │
│                                               │
│ 📅 Por Época:                                │
│ [📱 Modernos (2010+)] [🏛️ Clásicos (Pre-2000)] │
│ [🔥 Era Actual (2020+)] [💎 Era de Oro]      │
│                                               │
│ 🎯 Mantenimiento:                            │
│ [💔 Archivos Corruptos] [🔗 Enlaces Rotos]   │
│ [📊 Duplicados] [📏 Archivos Grandes]        │
└───────────────────────────────────────────────┘
```

### Búsqueda Inteligente

#### Sugerencias Automáticas
```python
class SearchSuggestionEngine:
    """Motor de sugerencias de búsqueda"""

    def get_suggestions(self, query):
        """Obtener sugerencias basadas en consulta parcial"""

        suggestions = []

        # 1. Sugerencias de títulos
        title_matches = self.search_titles(query)
        suggestions.extend(title_matches[:5])

        # 2. Sugerencias de editoriales
        publisher_matches = self.search_publishers(query)
        suggestions.extend(publisher_matches[:3])

        # 3. Sugerencias de volúmenes
        volume_matches = self.search_volumes(query)
        suggestions.extend(volume_matches[:5])

        # 4. Sugerencias de archivos
        file_matches = self.search_filenames(query)
        suggestions.extend(file_matches[:3])

        return suggestions[:10]  # Top 10 sugerencias
```

#### Corrección Automática
```python
def correct_search_query(query):
    """Corregir errores tipográficos en búsquedas"""

    corrections = {
        'batman': ['batmam', 'barman', 'batsman'],
        'spider-man': ['spiderman', 'spider man', 'spidre-man'],
        'superman': ['supermam', 'super man', 'supreman'],
        'dc comics': ['dc comic', 'dc', 'detective comics'],
        'marvel': ['marel', 'marevl', 'marvel comics']
    }

    # Usar algoritmo de distancia Levenshtein
    for correct, variants in corrections.items():
        for variant in variants:
            if calculate_similarity(query.lower(), variant) > 0.8:
                return correct

    return query
```

## 📊 Resultados de Búsqueda

### Presentación de Resultados

#### Vista de Grilla
```
┌─── Resultados: "batman 2016" (45 encontrados) ──┐
│                                                  │
│ 🖼️[Img] 🖼️[Img] 🖼️[Img] 🖼️[Img] 🖼️[Img]        │
│ Batman#1  Batman#2  Batman#3  Batman#4  Batman#5  │
│ ⭐⭐⭐⭐⭐ ⭐⭐⭐⭐   ⭐⭐⭐    ⭐⭐⭐⭐   ⭐⭐⭐⭐⭐│
│ 45.2MB    42.8MB    Sin Cat.  41.5MB    43.1MB   │
│                                                  │
│ 🖼️[Img] 🖼️[Img] 🖼️[Img] 🖼️[Img] 🖼️[Img]        │
│ Batman#6  Batman#7  Batman#8  Batman#9  Batman#10 │
│ ⭐⭐⭐⭐   ⭐⭐⭐⭐⭐  ⭐⭐⭐⭐   ⭐⭐⭐⭐   ⭐⭐⭐⭐⭐│
│ 44.7MB    46.3MB    43.9MB    42.1MB    45.8MB   │
│                                                  │
│ ◀️ Anterior  [1] 2 3 4 5  Siguiente ▶️          │
└──────────────────────────────────────────────────┘
```

#### Vista de Lista
```
┌─── Resultados: "batman 2016" (45 encontrados) ──┐
│                                                  │
│ ✅ Batman #1 - I Am Gotham                      │
│    📁 batman_001_2016.cbz | ⭐⭐⭐⭐⭐ | 45.2MB    │
│    📅 2016-06-15 | 🏷️ DC Comics                 │
│                                                  │
│ ✅ Batman #2 - I Am Gotham                      │
│    📁 batman_002_2016.cbz | ⭐⭐⭐⭐ | 42.8MB      │
│    📅 2016-07-06 | 🏷️ DC Comics                 │
│                                                  │
│ ❌ Batman #3 - I Am Gotham                      │
│    📁 batman_003_2016.cbz | Sin catalogar        │
│    📅 2016-07-20 | 🏷️ Sin editorial             │
│                                                  │
│ ✅ Batman #4 - I Am Gotham                      │
│    📁 batman_004_2016.cbz | ⭐⭐⭐⭐ | 41.5MB      │
│    📅 2016-08-03 | 🏷️ DC Comics                 │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Ordenamiento de Resultados

#### Opciones de Ordenamiento
```
Ordenar por:
○ Relevancia (defecto)    ○ Fecha de agregado
○ Título A-Z              ○ Título Z-A
○ Calidad (mayor)         ○ Calidad (menor)
○ Tamaño (mayor)          ○ Tamaño (menor)
○ Fecha de tapa (nuevo)   ○ Fecha de tapa (antiguo)
○ Editorial               ○ Número de issue
```

#### Algoritmo de Relevancia
```python
def calculate_search_relevance(comic, query):
    """Calcular relevancia de resultado de búsqueda"""

    relevance_score = 0.0

    # 1. Coincidencia exacta en título (peso: 40%)
    if query.lower() in comic.title.lower():
        relevance_score += 0.4

    # 2. Coincidencia en nombre de archivo (peso: 20%)
    if query.lower() in comic.filename.lower():
        relevance_score += 0.2

    # 3. Coincidencia en editorial (peso: 15%)
    if query.lower() in comic.publisher.lower():
        relevance_score += 0.15

    # 4. Coincidencia en volumen (peso: 15%)
    if query.lower() in comic.volume_name.lower():
        relevance_score += 0.15

    # 5. Coincidencia en descripción (peso: 10%)
    if query.lower() in comic.description.lower():
        relevance_score += 0.1

    # Bonus por calidad alta
    if comic.quality >= 4:
        relevance_score *= 1.1

    # Penalty por comics sin catalogar
    if not comic.is_cataloged:
        relevance_score *= 0.8

    return min(relevance_score, 1.0)
```

## 💾 Gestión de Filtros

### Filtros Guardados

#### Crear Filtro Personalizado
```
┌─── Crear Filtro Personalizado ───────────────────┐
│                                                  │
│ 📝 Nombre: [Comics Alta Calidad DC         ]    │
│                                                  │
│ 🔧 Configuración:                               │
│ ├── Editorial: DC Comics                        │
│ ├── Calidad: 4-5 ⭐                             │
│ ├── Año: 2010-2024                              │
│ ├── Estado: Solo clasificados                   │
│ └── Tamaño: 40-150 MB                           │
│                                                  │
│ 🎯 Vista Previa: 234 comics encontrados         │
│                                                  │
│ [💾 Guardar Filtro] [❌ Cancelar]               │
└──────────────────────────────────────────────────┘
```

#### Biblioteca de Filtros
```
┌─── Filtros Guardados ─────────────────────────────┐
│                                                   │
│ 📚 Mis Filtros:                                  │
│                                                   │
│ ⭐ Comics Alta Calidad DC                        │
│ ├── DC Comics, 4-5⭐, 2010-2024                  │
│ ├── 234 resultados                               │
│ └── [▶️ Aplicar] [✏️ Editar] [🗑️ Eliminar]        │
│                                                   │
│ 🕷️ Marvel Modernos Completos                     │
│ ├── Marvel, 2015+, Solo completos               │
│ ├── 89 resultados                                │
│ └── [▶️ Aplicar] [✏️ Editar] [🗑️ Eliminar]        │
│                                                   │
│ 🔧 Comics Para Mantenimiento                     │
│ ├── Sin catalogar, baja calidad                 │
│ ├── 167 resultados                               │
│ └── [▶️ Aplicar] [✏️ Editar] [🗑️ Eliminar]        │
│                                                   │
│ [➕ Crear Nuevo Filtro]                          │
└───────────────────────────────────────────────────┘
```

### Filtros Inteligentes

#### Auto-Filtros por Comportamiento
```python
class SmartFilterEngine:
    """Motor de filtros inteligentes"""

    def suggest_filters_based_on_usage(self, user_behavior):
        """Sugerir filtros basados en uso"""

        suggestions = []

        # Analizar patrones de búsqueda
        if user_behavior.searches_dc_frequently():
            suggestions.append({
                'name': 'Comics DC Frecuentes',
                'filters': {'publisher': 'DC Comics'},
                'reason': 'Buscas DC Comics frecuentemente'
            })

        # Analizar calidad preferida
        avg_quality = user_behavior.get_average_opened_quality()
        if avg_quality >= 4:
            suggestions.append({
                'name': 'Solo Alta Calidad',
                'filters': {'quality_min': 4},
                'reason': 'Prefieres comics de alta calidad'
            })

        # Analizar período temporal preferido
        preferred_years = user_behavior.get_preferred_year_range()
        if preferred_years:
            suggestions.append({
                'name': f'Comics {preferred_years[0]}-{preferred_years[1]}',
                'filters': {'year_range': preferred_years},
                'reason': f'Lees principalmente comics de {preferred_years[0]}-{preferred_years[1]}'
            })

        return suggestions
```

#### Filtros Contextuales
```
┌─── Filtros Sugeridos ─────────────────────────────┐
│                                                   │
│ 🤖 Basado en tu actividad reciente:              │
│                                                   │
│ 💡 "Solo Comics Modernos"                        │
│ ├── Lees principalmente comics 2015+             │
│ ├── 89% de tus lecturas son de esta era         │
│ └── [✅ Crear Filtro] [❌ Ignorar]                │
│                                                   │
│ 💡 "Marvel de Alta Calidad"                      │
│ ├── Prefieres Marvel con 4-5 ⭐                  │
│ ├── 78% de tus favoritos son Marvel HQ          │
│ └── [✅ Crear Filtro] [❌ Ignorar]                │
│                                                   │
│ 💡 "Series Incompletas"                          │
│ ├── Tienes 12 volúmenes <50% completos          │
│ ├── Te ayudará a priorizar adquisiciones        │
│ └── [✅ Crear Filtro] [❌ Ignorar]                │
└───────────────────────────────────────────────────┘
```

## 📊 Análisis de Búsquedas

### Estadísticas de Uso
```
┌─── Estadísticas de Búsqueda ──────────────────────┐
│                                                   │
│ 📊 Últimos 30 días:                              │
│                                                   │
│ 🔍 Total búsquedas: 234                          │
│ 📈 Promedio diario: 7.8                          │
│ ⏱️ Tiempo promedio: 2.3 seg                      │
│ 🎯 Tasa de éxito: 87.2%                          │
│                                                   │
│ 🔝 Términos más buscados:                        │
│ 1. batman (47 búsquedas)                         │
│ 2. spider-man (32 búsquedas)                     │
│ 3. dc comics (28 búsquedas)                      │
│ 4. 2023 (21 búsquedas)                           │
│ 5. high quality (18 búsquedas)                   │
│                                                   │
│ 🎛️ Filtros más usados:                           │
│ 1. Solo clasificados (89%)                       │
│ 2. Calidad 4-5⭐ (67%)                           │
│ 3. DC + Marvel (54%)                             │
│ 4. Últimos 5 años (43%)                          │
└───────────────────────────────────────────────────┘
```

### Optimización de Rendimiento
```python
def optimize_search_performance():
    """Optimizar rendimiento del sistema de búsqueda"""

    # 1. Índices de base de datos
    database_indexes = [
        "CREATE INDEX idx_comics_title ON comicbooks(title)",
        "CREATE INDEX idx_comics_filename ON comicbooks(filename)",
        "CREATE INDEX idx_comics_publisher ON comicbooks(publisher)",
        "CREATE INDEX idx_comics_quality ON comicbooks(quality)",
        "CREATE INDEX idx_comics_year ON comicbooks(cover_date)",
        "CREATE INDEX idx_comics_classification ON comicbooks(is_cataloged)",
        "CREATE INDEX idx_comics_size ON comicbooks(file_size)"
    ]

    # 2. Cache de búsquedas frecuentes
    search_cache = {
        'cache_size': 1000,
        'ttl_seconds': 3600,  # 1 hora
        'invalidate_on_change': True
    }

    # 3. Búsqueda asíncrona para grandes colecciones
    async_search_config = {
        'min_collection_size': 5000,
        'batch_size': 500,
        'max_concurrent_batches': 4
    }
```

---

**¿Quieres saber más sobre el sistema de thumbnails?** 👉 [Thumbnails](../funcionalidades/thumbnails.md)