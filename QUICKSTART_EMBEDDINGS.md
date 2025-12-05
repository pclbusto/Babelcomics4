# Inicio Rápido - Clasificación por Embeddings

## ¿Qué es esto?

Un sistema de clasificación automática de comics usando **inteligencia artificial visual**.

Compara las portadas de tus comics con las portadas de ComicVine y sugiere automáticamente qué ComicbookInfo corresponde a cada comic físico.

## Setup (Solo una vez)

Las dependencias ya están instaladas en el virtual environment `venv/`.

Si necesitas reinstalar:

```bash
./setup_embeddings.sh
```

## Flujo de Trabajo Completo

### Paso 1: Generar Embeddings de ComicVine

Primero necesitas generar los embeddings de las covers que descargaste de ComicVine:

```bash
./venv/bin/python generate_cover_embeddings.py
```

Esto puede tardar dependiendo de cuántas covers tengas:
- ~1-2 segundos por cover (CPU)
- ~0.3-0.5 segundos por cover (GPU)

**Solo necesitas hacer esto una vez** (y cuando descargues nuevos volúmenes).

### Paso 2: Probar con Unos Pocos Comics

Empieza con un test pequeño para ver cómo funciona:

```bash
./venv/bin/python auto_classify_comics.py --max 5
```

Esto te mostrará:
- Qué comics sin clasificar encontró
- Qué ComicbookInfo es más similar (título + número)
- El % de similaridad
- Si pasa el umbral (75% por defecto)

**NO aplica cambios**, solo muestra sugerencias.

### Paso 3: Aplicar Clasificaciones

Si las sugerencias se ven bien, aplícalas:

```bash
./venv/bin/python auto_classify_comics.py --max 20 --auto-apply
```

Esto SÍ actualiza la base de datos.

### Paso 4: Procesar Toda la Colección

Una vez que estés confiado:

```bash
# Con umbral conservador (solo muy buenas coincidencias)
./venv/bin/python auto_classify_comics.py --threshold 0.80 --auto-apply

# Luego con umbral más permisivo para los que quedaron
./venv/bin/python auto_classify_comics.py --threshold 0.70 --auto-apply
```

## Ajustando el Umbral

El **umbral** (threshold) determina cuán similar debe ser la portada:

- `0.90` (90%): Solo coincidencias casi perfectas
  - Muy pocos falsos positivos
  - Muchos comics quedarán sin clasificar
  - **Usar**: Si tienes covers muy similares entre diferentes comics

- `0.80` (80%): Coincidencias muy buenas (RECOMENDADO)
  - Balance ideal
  - Pocas incorrectas
  - **Usar**: Para empezar

- `0.75` (75%): Coincidencias buenas (DEFAULT)
  - Más permisivo
  - Clasifica más comics
  - Algunas pueden ser incorrectas
  - **Usar**: Después de probar con 0.80

- `0.60` (60%): Coincidencias razonables
  - Muy permisivo
  - Clasifica mucho más
  - Más riesgo de errores
  - **Usar**: Para comics difíciles de clasificar, revisando manualmente

## Interpretando los Resultados

```bash
[1/50] ✓ Batman 001.cbz
    → Batman (2016) #1 (similaridad: 89.45%)
    → APLICADO
```
- `✓` = Clasificado exitosamente
- `89.45%` = Muy alta confianza
- `APLICADO` = Se guardó en la BD (solo con --auto-apply)

```bash
[2/50] ⊘ Superman 001.cbr
    → Mejor coincidencia: Superman Unchained #1 (64.22%)
    → Similaridad bajo el umbral 75.00%
```
- `⊘` = No clasificado
- `64.22%` = Similaridad baja
- Se omite porque no alcanza el umbral

```bash
[3/50] ⊘ Comic sin thumbnail.cbz - Sin thumbnail
```
- No tiene thumbnail generado
- Genera thumbnails primero desde la app principal

## Tips y Trucos

### 1. Generar Thumbnails Primero

Desde la aplicación principal, escanea tu colección para que genere thumbnails de todos los comics.

### 2. Estrategia de Múltiples Pasadas

```bash
# Primera pasada: Solo las muy obvias (90%)
./venv/bin/python auto_classify_comics.py --threshold 0.90 --auto-apply

# Segunda pasada: Buenas coincidencias (80%)
./venv/bin/python auto_classify_comics.py --threshold 0.80 --auto-apply

# Tercera pasada: Razonables (70%)
./venv/bin/python auto_classify_comics.py --threshold 0.70 --auto-apply

# Los que quedan, revisar manualmente
./venv/bin/python auto_classify_comics.py --threshold 0.60
```

### 3. Procesar en Lotes

Si tienes muchos comics:

```bash
# Procesa de 50 en 50
./venv/bin/python auto_classify_comics.py --max 50 --auto-apply

# Ejecuta varias veces hasta procesar todos
```

### 4. Ver Solo Sugerencias Sin Aplicar

Siempre puedes ejecutar sin `--auto-apply` para ver qué haría:

```bash
./venv/bin/python auto_classify_comics.py --threshold 0.70
```

### 5. Actualizar Embeddings Incrementalmente

Después de descargar nuevos volúmenes:

```bash
./venv/bin/python generate_cover_embeddings.py
```

Solo procesará las covers nuevas que no tienen embedding.

## Casos Especiales

### Comics con Portadas Variantes

Si un comic físico tiene una portada variante, puede que no coincida exactamente. El sistema buscará la más similar de todas las covers disponibles.

### Múltiples Comics del Mismo Issue

Si tienes varias copias del mismo comic, el sistema los clasificará todos con el mismo ComicbookInfo (que es correcto).

### Comics sin Metadata en ComicVine

Si un comic no está en ComicVine, no podrás clasificarlo automáticamente. Tendrás que hacerlo manual.

## Verificar Resultados

Después de clasificar:

1. Abre Babelcomics4
2. Ve a la vista de Comics
3. Verifica algunos de los clasificados
4. Si hay errores, puedes reclasificar manualmente

## ¿Funciona Bien?

**Funciona muy bien cuando**:
- Las portadas son de la misma edición
- La imagen del comic es clara
- Tienes las covers de ComicVine descargadas

**Puede fallar cuando**:
- Portadas variantes muy diferentes
- Covers de diferentes ediciones (mismo contenido, diferente arte)
- Thumbnails de mala calidad
- Comics sin información en ComicVine

**Precisión esperada**:
- Con umbral 0.80: ~85-90% de aciertos
- Con umbral 0.75: ~80-85% de aciertos
- Con umbral 0.70: ~70-80% de aciertos

Siempre es bueno revisar una muestra de los resultados.

## Archivos Creados

- `helpers/embedding_generator.py` - Motor de embeddings
- `generate_cover_embeddings.py` - Script para covers de ComicVine
- `auto_classify_comics.py` - Script de clasificación
- `test_embeddings.py` - Script de prueba
- `venv/` - Virtual environment con dependencias
- Columnas en BD:
  - `comicbooks_info_covers.embedding`
  - `comicbooks.embedding`

## ¿Preguntas?

Consulta `EMBEDDINGS_README.md` para más detalles técnicos.
