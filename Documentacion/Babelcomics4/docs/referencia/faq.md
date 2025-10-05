# FAQ - Preguntas Frecuentes

Esta sección responde a las preguntas más frecuentes sobre Babelcomics4, desde conceptos básicos hasta funcionalidades avanzadas y solución de problemas comunes.

## 🤔 Preguntas Generales

### ¿Qué es Babelcomics4?

**Babelcomics4** es un gestor moderno de colecciones de comics digitales desarrollado en Python con GTK4. Permite organizar, catalogar y gestionar tu biblioteca de comics con integración a ComicVine para obtener metadatos automáticamente.

**Características principales:**
- Soporte para formatos CBZ, CBR, PDF
- Catalogación automática con ComicVine API
- Interfaz moderna con GTK4 y libadwaita
- Sistema de thumbnails con efectos visuales
- Búsqueda y filtrado avanzado
- Gestión de volúmenes y series

### ¿En qué sistemas operativos funciona?

Babelcomics4 es multiplataforma y funciona en:

- **Linux** (Ubuntu, Fedora, Arch, openSUSE, etc.)
- **Windows** 10/11 (con WSL o nativo)
- **macOS** (con Homebrew)

**Requisitos mínimos:**
- Python 3.9+
- GTK4 4.8+
- libadwaita 1.2+
- 4GB RAM
- 1GB espacio libre

### ¿Es gratuito?

Sí, Babelcomics4 es completamente **gratuito y de código abierto**. Puedes usar, modificar y distribuir el software libremente bajo los términos de la licencia.

### ¿Necesito una cuenta de ComicVine?

No necesitas una cuenta, pero sí necesitas una **API Key gratuita** de ComicVine para usar las funciones de catalogación automática.

**Para obtener una API Key:**
1. Ve a [ComicVine](https://comicvine.gamespot.com)
2. Crea una cuenta gratuita
3. Solicita una API Key en tu perfil
4. Configúrala en Babelcomics4

## 📚 Gestión de Comics

### ¿Qué formatos de comics soporta?

Babelcomics4 soporta los siguientes formatos:

| Formato | Extensión | Soporte | Notas |
|---------|-----------|---------|--------|
| Comic Book ZIP | `.cbz` | ✅ Completo | Recomendado |
| Comic Book RAR | `.cbr` | ✅ Completo | Requiere unrar |
| PDF | `.pdf` | ✅ Básico | Soporte limitado |
| Imágenes | `.jpg`, `.png` | ⚠️ Carpetas | Carpetas con imágenes |
| EPUB | `.epub` | 🔄 Planificado | Próxima versión |

### ¿Cómo importo mi colección existente?

**Método 1: Escaneo automático**
1. Configura tus directorios de comics en **Preferencias** → **Directorios**
2. La aplicación escaneará automáticamente al iniciar
3. Los comics aparecerán sin catalogar (en escala de grises)

**Método 2: Importación manual**
1. **Archivo** → **Importar Comics**
2. Selecciona el directorio de tu colección
3. Confirma el escaneo recursivo

**Método 3: Arrastrar y soltar**
1. Arrastra archivos o carpetas a la ventana
2. Se importarán automáticamente

### ¿Puedo organizar mis comics en subcarpetas?

Sí, Babelcomics4 respeta tu organización de carpetas y escanea recursivamente. Ejemplos de organización:

```
Comics/
├── DC/
│   ├── Batman/
│   │   ├── Batman_001.cbz
│   │   └── Batman_002.cbz
│   └── Superman/
├── Marvel/
│   ├── Spider-Man/
│   └── X-Men/
└── Independent/
    ├── Image/
    └── Dark_Horse/
```

### ¿Qué significan los colores de los thumbnails?

Los thumbnails usan efectos visuales para mostrar el estado:

- **🌈 Color normal**: Comic catalogado con ComicVine
- **⚫ Escala de grises**: Comic sin catalogar
- **🔴 Desaturado**: Comic en papelera
- **⭐ Con estrellas**: Overlay de calidad (1-5 estrellas)

### ¿Cómo califico mis comics?

Puedes calificar comics de varias formas:

**Método 1: Click en estrellas**
- Click en las estrellas del thumbnail
- Calificación de 1-5 estrellas

**Método 2: Vista de detalle**
- Abre el comic en vista detallada
- Ajusta la calificación en el panel lateral

**Método 3: Edición en lote**
- Selecciona múltiples comics
- Click derecho → **Cambiar Calidad**

## 🔍 Búsqueda y Filtros

### ¿Cómo busco comics específicos?

Babelcomics4 ofrece múltiples métodos de búsqueda:

**Búsqueda básica:**
- Escribe en la barra de búsqueda
- Busca en títulos, archivos, editoriales

**Búsqueda avanzada:**
- Usa operadores: `batman AND year:2018`
- Filtros por campo: `publisher:"DC Comics"`
- Rangos: `quality:4..5`

**Filtros visuales:**
- Panel de filtros lateral
- Filtros rápidos en la barra superior
- Filtros guardados personalizados

### ¿Puedo guardar mis búsquedas favoritas?

Sí, puedes crear **filtros guardados**:

1. Configura tus filtros deseados
2. Click en **💾 Guardar Filtro**
3. Asigna nombre y descripción
4. Accede desde el panel lateral

**Ejemplo de filtros útiles:**
- "DC Alta Calidad": DC Comics con 4-5 estrellas
- "Sin Catalogar": Comics pendientes de catalogación
- "Agregados Hoy": Comics importados recientemente

### ¿Cómo filtro por editorial o año?

**Por editorial:**
- Panel de filtros → **Editorial**
- Selecciona checkboxes de editoriales deseadas
- O busca: `publisher:"Marvel Comics"`

**Por año:**
- Panel de filtros → **Rango de Años**
- Ajusta deslizadores de año inicio/fin
- O busca: `year:2018..2023`

**Por década:**
- Usa presets rápidos: "2020s", "2010s", etc.
- O filtros personalizados por rango

## 🌐 ComicVine

### ¿Qué es ComicVine y por qué lo necesito?

**ComicVine** es la base de datos de comics más completa del mundo, propiedad de GameSpot. Proporciona:

- Metadatos detallados de comics
- Información de volúmenes y series
- Portadas de alta calidad
- Equipos creativos y personajes
- Fechas de publicación precisas

**Beneficios de la integración:**
- Catalogación automática
- Información rica y precisa
- Portadas profesionales
- Organización por volúmenes

### ¿Por qué algunos comics no se catalogan automáticamente?

Varios factores pueden impedir la catalogación automática:

**Problemas de nomenclatura:**
- Nombres de archivo poco claros
- Falta de información de número/año
- Caracteres especiales problemáticos

**Limitaciones de ComicVine:**
- Comics muy antiguos o raros
- Editoriales independientes pequeñas
- Publicaciones no oficiales

**Configuración restrictiva:**
- Umbral de confianza muy alto
- Filtros de editorial restrictivos

**Soluciones:**
1. Renombrar archivos con formato estándar
2. Catalogación manual desde búsqueda
3. Ajustar umbral de confianza
4. Mejorar nombres de series

### ¿Cómo obtengo una API Key de ComicVine?

**Paso a paso:**
1. Ve a [comicvine.gamespot.com](https://comicvine.gamespot.com)
2. **Registrarse** (gratuito)
3. Ve a tu **perfil de usuario**
4. Click en **API** en el menú
5. **Solicitar API Key**
6. Espera aprobación (24-48 horas)
7. Copia la key a Babelcomics4

**En Babelcomics4:**
1. **Preferencias** → **ComicVine**
2. Pega tu API Key
3. **Guardar** y reiniciar

### ¿Hay límites en el uso de ComicVine?

Sí, ComicVine tiene límites de uso:

- **200 peticiones por hora** (límite estándar)
- **1 petición cada 3 segundos** (rate limiting)
- **Sin uso comercial** sin permiso explícito

**Babelcomics4 gestiona esto automáticamente:**
- Rate limiting integrado
- Cache de respuestas
- Procesamientos en lote
- Delays configurables

### ¿Puedo usar Babelcomics4 sin ComicVine?

Sí, puedes usar Babelcomics4 sin ComicVine, pero con limitaciones:

**Funcionalidades disponibles sin ComicVine:**
- ✅ Importar y organizar comics
- ✅ Búsqueda por nombre de archivo
- ✅ Calificación manual
- ✅ Thumbnails básicos
- ✅ Filtros por tamaño/formato

**Funcionalidades que requieren ComicVine:**
- ❌ Catalogación automática
- ❌ Metadatos ricos (sinopsis, fechas)
- ❌ Organización por volúmenes
- ❌ Información de equipos creativos
- ❌ Portadas oficiales

## ⚙️ Configuración y Personalización

### ¿Dónde se almacenan mis datos?

Babelcomics4 almacena datos en ubicaciones estándar del sistema:

**Linux:**
```
~/.config/babelcomics4/          # Configuración
~/.local/share/babelcomics4/     # Datos de aplicación
├── database/babelcomics.db      # Base de datos principal
├── thumbnails/                  # Cache de thumbnails
├── covers/                      # Portadas descargadas
└── logs/                        # Archivos de log
```

**Windows:**
```
%APPDATA%\Babelcomics4\          # Configuración
%LOCALAPPDATA%\Babelcomics4\     # Datos de aplicación
```

**macOS:**
```
~/Library/Preferences/com.babelcomics4/        # Configuración
~/Library/Application Support/Babelcomics4/    # Datos
```

### ¿Puedo cambiar el tamaño de los thumbnails?

Sí, puedes personalizar los thumbnails:

**En Preferencias → Thumbnails:**
- **Tamaño**: Pequeño, Mediano, Grande, Extra Grande
- **Calidad**: Económica, Balanceada, Alta
- **Efectos**: Escala de grises, overlays, bordes

**Configuración avanzada en config.json:**
```json
{
  "thumbnails": {
    "size": "large",
    "quality": "high",
    "cache_size_limit": "2GB",
    "effects": {
      "uncataloged_grayscale": true,
      "quality_overlay": true
    }
  }
}
```

### ¿Cómo hago backup de mi colección?

**Backup automático (recomendado):**
1. **Preferencias** → **Base de Datos**
2. Activar **Backup Automático**
3. Configurar frecuencia (diaria/semanal)

**Backup manual:**
```bash
# Backup completo
cp -r ~/.local/share/babelcomics4/ ~/backup_babelcomics4/

# Solo base de datos
cp ~/.local/share/babelcomics4/database/babelcomics.db ~/backup_db.db

# Desde la aplicación
babelcomics4 --backup
```

**Restaurar backup:**
```bash
# Restaurar completo
cp -r ~/backup_babelcomics4/ ~/.local/share/babelcomics4/

# Solo base de datos
cp ~/backup_db.db ~/.local/share/babelcomics4/database/babelcomics.db
```

### ¿Puedo usar Babelcomics4 en múltiples dispositivos?

Sí, hay varias estrategias:

**Opción 1: Sincronización de configuración**
- Exportar/importar configuración
- Compartir archivo `config.json`

**Opción 2: Base de datos compartida**
- Base de datos en almacenamiento de red (NAS)
- Configurar ruta personalizada de BD

**Opción 3: Directorio compartido**
- Comics en almacenamiento de red
- Cada dispositivo con su propia BD

**Configuración para red:**
```json
{
  "database": {
    "path": "/shared/babelcomics/database.db"
  },
  "directories": {
    "comics_paths": ["/shared/comics/"]
  }
}
```

## 🔧 Problemas Técnicos

### La aplicación va lenta, ¿qué puedo hacer?

**Diagnóstico rápido:**
```bash
# Ejecutar diagnóstico automático
babelcomics4 --diagnose

# Verificar recursos del sistema
htop  # Linux
taskmgr  # Windows
```

**Optimizaciones comunes:**

**1. Limpiar cache de thumbnails:**
```bash
rm -rf ~/.local/share/babelcomics4/thumbnails/*
```

**2. Optimizar base de datos:**
```bash
babelcomics4 --vacuum-db
```

**3. Reducir calidad de thumbnails:**
```json
{
  "thumbnails": {
    "quality": "economy",
    "size": "small"
  }
}
```

**4. Limitar tamaño de colección mostrada:**
```json
{
  "interface": {
    "items_per_page": 25,
    "lazy_loading": true
  }
}
```

### ¿Por qué faltan thumbnails?

**Causas comunes:**
- Archivos corruptos o inaccesibles
- Falta de permisos de escritura
- Cache lleno o corrupto
- Formato de archivo no soportado

**Soluciones:**
```bash
# Regenerar thumbnails faltantes
babelcomics4 --regenerate-thumbnails

# Limpiar cache corrupto
rm -rf ~/.local/share/babelcomics4/thumbnails/*

# Verificar permisos
chmod 755 ~/.local/share/babelcomics4/thumbnails/

# Verificar archivos corruptos
babelcomics4 --verify-files
```

### Error: "Base de datos bloqueada"

**Causas:**
- Múltiples instancias ejecutándose
- Cierre abrupto anterior
- Problemas de permisos

**Soluciones:**
```bash
# 1. Cerrar todas las instancias
pkill babelcomics4

# 2. Eliminar archivos de bloqueo
rm ~/.local/share/babelcomics4/database/*.lock

# 3. Verificar integridad
sqlite3 ~/.local/share/babelcomics4/database/babelcomics.db "PRAGMA integrity_check;"

# 4. Si hay corrupción
babelcomics4 --repair-database
```

### No puedo conectar con ComicVine

**Verificaciones:**
1. **Conectividad de red:**
```bash
ping comicvine.gamespot.com
curl -I https://comicvine.gamespot.com
```

2. **API Key válida:**
```bash
# Probar API Key
curl "https://comicvine.gamespot.com/api/volumes/?api_key=TU_API_KEY&format=json&limit=1"
```

3. **Configuración de proxy:**
```json
{
  "network": {
    "proxy": "http://proxy.empresa.com:8080",
    "timeout": 30
  }
}
```

4. **Rate limiting:**
```json
{
  "comicvine": {
    "request_delay": 2.0,
    "requests_per_hour": 100
  }
}
```

## 🚀 Funcionalidades Avanzadas

### ¿Puedo personalizar la interfaz?

Sí, Babelcomics4 ofrece varias opciones de personalización:

**Temas:**
- Automático (sigue el sistema)
- Claro
- Oscuro
- Personalizado (CSS)

**Diseño:**
- Tamaño de tarjetas
- Densidad de información
- Orden de columnas
- Paneles colapsables

**Accesibilidad:**
- Soporte para lectores de pantalla
- Navegación por teclado
- Contraste alto
- Tamaños de fuente ajustables

### ¿Hay atajos de teclado?

Sí, Babelcomics4 incluye atajos de teclado completos:

**Navegación:**
- `Ctrl+F`: Buscar
- `Ctrl+1/2/3`: Cambiar vistas
- `F5`: Actualizar/Escanear
- `Escape`: Limpiar búsqueda

**Gestión:**
- `Ctrl+A`: Seleccionar todo
- `Ctrl+D`: Deseleccionar
- `Delete`: Mover a papelera
- `Ctrl+Z`: Deshacer

**ComicVine:**
- `Ctrl+U`: Actualizar desde ComicVine
- `Ctrl+Shift+C`: Catalogar seleccionados

**Personalizables:**
```json
{
  "shortcuts": {
    "search": "Ctrl+F",
    "catalog": "Ctrl+Shift+C",
    "quality_up": "Plus",
    "quality_down": "Minus"
  }
}
```

### ¿Puedo exportar mi catálogo?

Sí, Babelcomics4 permite exportar datos en varios formatos:

**Formatos disponibles:**
- **CSV**: Para hojas de cálculo
- **JSON**: Para otros programas
- **XML**: Para ComicBookDB
- **HTML**: Para web personal

**Ejemplo de exportación:**
```bash
# Exportar toda la colección
babelcomics4 --export-csv ~/mi_coleccion.csv

# Exportar solo DC Comics
babelcomics4 --export-csv ~/dc_comics.csv --filter publisher:"DC Comics"

# Exportar con metadatos completos
babelcomics4 --export-json ~/coleccion_completa.json --include-metadata
```

### ¿Hay plugins o extensiones?

Actualmente Babelcomics4 no tiene un sistema de plugins formal, pero es extensible:

**Extensibilidad actual:**
- Scripts personalizados
- Configuración avanzada JSON
- Integración con herramientas externas

**Extensiones planificadas:**
- Sistema de plugins Python
- Hooks para eventos
- Temas personalizados
- Integraciones con servicios

## 📞 Soporte y Comunidad

### ¿Dónde puedo obtener ayuda?

**Recursos oficiales:**
- 📚 **Documentación**: Esta misma documentación
- 🐛 **Reportar bugs**: GitHub Issues
- 💬 **Comunidad**: Foro de usuarios
- 💡 **Sugerencias**: GitHub Discussions

**Información útil para soporte:**
```bash
# Información del sistema
babelcomics4 --version
babelcomics4 --system-info

# Logs de diagnóstico
babelcomics4 --collect-logs

# Estado de la aplicación
babelcomics4 --diagnose
```

### ¿Cómo contribuyo al proyecto?

¡Las contribuciones son bienvenidas!

**Formas de contribuir:**
- 🐛 Reportar bugs y problemas
- 💡 Sugerir nuevas funcionalidades
- 📝 Mejorar documentación
- 🌍 Traducir a otros idiomas
- 💻 Contribuir código

**Para desarrolladores:**
1. Fork del repositorio
2. Crear rama de feature
3. Implementar cambios
4. Tests y documentación
5. Pull request

### ¿Habrá más funcionalidades?

Sí, Babelcomics4 está en desarrollo activo. **Funcionalidades planificadas:**

**Próxima versión (4.1):**
- Soporte para EPUB
- Modo de lectura integrado
- Sincronización en la nube
- Sistema de plugins

**Futuro (4.x):**
- Integración con más APIs
- Modo servidor web
- Aplicación móvil compañera
- AI para catalogación

**Roadmap público:**
- GitHub Projects
- Discusiones de la comunidad
- Encuestas de funcionalidades

---

**¿No encuentras tu pregunta?** 👉 [Contacto y Soporte](troubleshooting.md#obtener-ayuda)