# Sistema de Clasificación Automática por Embeddings

Este sistema permite clasificar automáticamente comics físicos usando embeddings visuales de sus covers.

## ¿Cóó funciona?

1. **Genera embeddings** de todas las covers de ComicbookInfo (metadatos de ComicVine)
2. **Genera embeddings** de las covers de tus comics físicos sin clasificar
3. **Compara** los embeddings usando similaridad coseno
4. **Sugiere** el ComicbookInfo más similar visualmente

## Instalación de Dependencias

**IMPORTANTE**: Este proyecto usa un virtual environment para las dependencias de ML.

### Para GPU GTX 1070 (o GPUs viejas con CUDA < 7.0)

Requiere Python 3.11 y PyTorch 1.13.1:

```bash
# Script automático (recomendado)
./install_gpu_support.sh

# O manual:
python3.11 -m venv .venv
./.venv/bin/pip install torch==1.13.1+cu117 --extra-index-url https://download.pytorch.org/whl/cu117
./.venv/bin/pip install transformers==4.25.1 "numpy<2" pillow sqlalchemy requests
```

**Rendimiento GPU**: ~0.1-0.2 seg/imagen (~1.5 horas para 50K covers)

### Para CPU o GPU moderna (RTX 3000+)

Usar Python 3.13 y versiones nuevas:

```bash
python3 -m venv venv
./venv/bin/pip install torch transformers numpy pillow sqlalchemy requests
```

**Rendimiento CPU**: ~2-3 seg/imagen (~37 horas para 50K covers)

## Uso

### 1. Probar el sistema

```bash
./venv/bin/python test_embeddings.py
```

Verifica que el modelo CLIP se carga correctamente y puede generar embeddings.

### 2. Generar embeddings de ComicbookInfo covers

```bash
./venv/bin/python generate_cover_embeddings.py
```

Esto procesará todas las covers descargadas de ComicVine y generará sus embeddings.
**Solo necesitas hacer esto una vez**, y luego cuando descargues nuevos volúmenes.

### 3. Clasificar automáticamente tus comics

**Modo sugerencia** (solo muestra, no aplica):
```bash
./venv/bin/python auto_classify_comics.py
```

**Modo automático** (aplica las clasificaciones):
```bash
./venv/bin/python auto_classify_comics.py --auto-apply
```

**Con umbral personalizado**:
```bash
# Solo acepta coincidencias con >85% de similaridad
./venv/bin/python auto_classify_comics.py --threshold 0.85 --auto-apply
```

**Procesar solo algunos comics**:
```bash
# Procesa solo los primeros 10 comics
./venv/bin/python auto_classify_comics.py --max 10
```

## Parámetros

### auto_classify_comics.py

- `--threshold FLOAT`: Umbral mínimo de similaridad (0.0-1.0, default: 0.75)
  - 0.75 = 75% similar (recomendado para empezar)
  - 0.85 = 85% similar (más estricto, menos falsos positivos)
  - 0.60 = 60% similar (más permisivo, puede clasificar más pero con más errores)

- `--auto-apply`: Aplicar automáticamente las clasificaciones
  - Sin esta opción, solo muestra sugerencias
  - Con esta opción, actualiza la base de datos

- `--max N`: Procesar solo N comics
  - Útil para probar con un subset pequeño

## Ejemplos de Uso

### Workflow recomendado

```bash
# 1. Prueba inicial (primeros 5 comics, solo ver sugerencias)
./venv/bin/python auto_classify_comics.py --max 5

# 2. Si se ve bien, aplicar a los primeros 20
./venv/bin/python auto_classify_comics.py --max 20 --auto-apply

# 3. Si sigue bien, procesar todo con umbral moderado
./venv/bin/python auto_classify_comics.py --threshold 0.80 --auto-apply

# 4. Para los que quedaron sin clasificar, bajar el umbral
./venv/bin/python auto_classify_comics.py --threshold 0.70 --auto-apply
```

### Regenerar embeddings de covers nuevas

```bash
# Después de descargar nuevos volúmenes de ComicVine
./venv/bin/python generate_cover_embeddings.py
```

## Rendimiento

- **Primera ejecución**: Descarga el modelo CLIP (~600MB)
- **Generación de embeddings**: ~0.5-2 segundos por imagen (dependiendo de GPU/CPU)
- **Búsqueda**: Muy rápida una vez que los embeddings están generados

### Con GPU
Si tienes una GPU CUDA, el proceso será mucho más rápido.
El sistema la detecta automáticamente.

### Sin GPU
Funciona perfectamente con CPU, solo es más lento (~2-3 segundos por imagen).

## Notas Técnicas

- **Modelo**: OpenAI CLIP (clip-vit-base-patch32)
- **Dimensiones**: 512-dimensional embeddings
- **Similaridad**: Cosine similarity (producto punto de vectores normalizados)
- **Almacenamiento**: JSON strings en SQLite

## Troubleshooting

### "No se encuentra la base de datos"
```bash
# Asegúrate de estar en el directorio correcto
cd /home/pedro/PycharmProjects/Babelcomics4
```

### "No hay covers con embeddings"
```bash
# Ejecuta primero el generador de embeddings
python3 generate_cover_embeddings.py
```

### "Sin thumbnail" para muchos comics
```bash
# Genera thumbnails primero desde la aplicación principal
python3 Babelcomic4.py
# Y escanea tu colección
```

### Error de memoria
```bash
# Procesa en lotes más pequeños
./venv/bin/python auto_classify_comics.py --max 50 --auto-apply
# Luego ejecuta de nuevo para los siguientes 50
```

## Integración Futura en la UI

Próximos pasos para integrar esto en la interfaz gráfica:

1. Botón "Clasificar Automáticamente" en la vista de comics
2. Progreso visual durante la clasificación
3. Confirmación manual de sugerencias con vista previa
4. Generación automática de embeddings al descargar covers

## Archivos Creados

- `helpers/embedding_generator.py`: Clase para generar y comparar embeddings
- `generate_cover_embeddings.py`: Script para procesar covers de ComicbookInfo
- `auto_classify_comics.py`: Script de clasificación automática
- `test_embeddings.py`: Script de prueba
- Columnas agregadas a BD:
  - `comicbooks_info_covers.embedding`
  - `comicbooks.embedding`
