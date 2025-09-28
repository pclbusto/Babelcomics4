# Babelcomics4 - Gestor de Colección de Comics

![Logo Babelcomics4](https://img.shields.io/badge/Babelcomics4-v4.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.13-green.svg)
![GTK4](https://img.shields.io/badge/GTK4-4.0-orange.svg)

Babelcomics4 es un gestor completo de colecciones de comics desarrollado en Python con GTK4 y libadwaita. Permite organizar, catalogar y gestionar tu colección de comics digitales con integración directa a ComicVine API.

## 🚀 Características Principales

### 📚 Gestión Completa
- **Comics Digitales**: Soporte para archivos CBZ, CBR y formatos de imagen
- **Metadatos**: Información detallada de cada comic con integración ComicVine
- **Thumbnails**: Generación automática de miniaturas con efectos visuales
- **Búsqueda Avanzada**: Filtros potentes por clasificación, calidad, año, etc.

### 🎨 Interfaz Moderna
- **GTK4 + libadwaita**: Interfaz nativa y moderna
- **Navegación Fluida**: NavigationView con páginas de detalle
- **Modo Oscuro**: Soporte completo para temas claros y oscuros
- **Responsive**: Adaptable a diferentes tamaños de pantalla

### 🔗 Integración ComicVine
- **API Oficial**: Conexión directa con la base de datos ComicVine
- **Actualización Automática**: Descarga de metadatos e imágenes en segundo plano
- **Threading**: Descargas concurrentes sin bloquear la interfaz
- **Cache Inteligente**: Sistema de cache para optimizar rendimiento

### 🗃️ Base de Datos Robusta
- **SQLAlchemy ORM**: Gestión avanzada de datos relacionales
- **Modelos Estructurados**: Comics, Volúmenes, Editoriales y más
- **Migración Automática**: Actualizaciones de esquema sin pérdida de datos
- **Backup Automático**: Protección de tu colección

## 🎯 Funcionalidades Destacadas

### Catalogación Inteligente
- Escaneo automático de directorios
- Detección de metadatos por nombre de archivo
- Asociación automática con volúmenes ComicVine
- Generación de thumbnails en tiempo real

### Filtros Avanzados
- **Clasificación**: Distingue entre comics catalogados y sin catalogar
- **Visual**: Thumbnails en escala de grises para issues sin físicos
- **Calidad**: Sistema de puntuación por estrellas
- **Estado**: Exclusión de elementos en papelera

### Gestión de Volúmenes
- Vista detallada con lista de issues
- Botón de actualización ComicVine
- Información de completitud de colección
- Navegación fluida entre volúmenes e issues

## 📊 Estadísticas del Proyecto

```
📁 Estructura del Proyecto
├── 🐍 Python Backend (SQLAlchemy + ComicVine API)
├── 🖥️ GTK4/libadwaita Frontend
├── 🗄️ Sistema de Repositorios
├── 🖼️ Generador de Thumbnails
├── 🔍 Motor de Búsqueda
└── 📚 Documentación MkDocs
```

## 🛠️ Tecnologías Utilizadas

- **Python 3.13**: Lenguaje principal
- **GTK4**: Toolkit de interfaz gráfica
- **libadwaita**: Componentes modernos de GNOME
- **SQLAlchemy**: ORM para base de datos
- **Pillow**: Procesamiento de imágenes
- **Requests**: Cliente HTTP para ComicVine API
- **Threading**: Concurrencia y paralelismo

## 📖 Guía Rápida

1. **[Instalación](usuario/instalacion.md)**: Configura tu entorno de desarrollo
2. **[Primeros Pasos](usuario/primeros-pasos.md)**: Aprende lo básico
3. **[Gestión de Comics](usuario/gestion-comics.md)**: Organiza tu colección
4. **[ComicVine](usuario/comicvine.md)**: Conecta con la API
5. **[Filtros](usuario/filtros-busqueda.md)**: Encuentra comics específicos

## 🎨 Capturas de Pantalla

### Vista Principal
La interfaz principal muestra tu colección con thumbnails generados automáticamente:

- Vista de grid responsiva
- Información básica de cada comic
- Estado visual (clasificado/sin clasificar)
- Búsqueda en tiempo real

### Detalle de Volumen
Navegación completa por volúmenes con:

- Lista de todos los issues
- Botón de actualización ComicVine
- Información de metadatos
- Estadísticas de colección

### Filtros Avanzados
Sistema de filtrado potente:

- Clasificación (catalogados/sin catalogar)
- Rango de calidad (1-5 estrellas)
- Exclusión de papelera
- Múltiples criterios combinables

## 🤝 Contribuir

Este proyecto está en desarrollo activo. Las contribuciones son bienvenidas:

1. Fork del repositorio
2. Crear rama de feature
3. Implementar mejoras
4. Tests y documentación
5. Pull request

## 📝 Licencia

Proyecto desarrollado para gestión personal de colecciones de comics digitales.

---

**¿Listo para empezar?** 👉 [Instalación](usuario/instalacion.md)
