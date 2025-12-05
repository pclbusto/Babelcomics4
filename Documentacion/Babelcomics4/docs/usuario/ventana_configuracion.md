# Configuración del Sistema

La ventana de configuración permite ajustar el comportamiento global de BabelComics4, definir las rutas de almacenamiento, conectar servicios externos y optimizar el rendimiento del sistema.

El panel se divide en dos pestañas principales: **General** y **Avanzado**.

---

## 1. Pestaña General

En esta sección se definen las conexiones externas, las rutas de archivos críticas y la personalización de la interfaz de usuario.

![Pestaña de Configuración General](Imagenes/configuracion_general.png)

### **ComicVine API**
Configuración esencial para que el sistema pueda descargar metadatos y portadas.
* **API Key:** Campo para ingresar tu clave personal de ComicVine (obtenible en comicvine.gamespot.com).
* **Validar Conexión (Botón "Probar"):** Verifica que la clave sea correcta y que haya comunicación con el servidor.
* **Intervalo entre requests:** Define el tiempo de espera (en segundos) entre cada petición a la API.
    * *Recomendación:* Mantener en **0.5s** o superior para evitar bloqueos por exceso de tráfico.
* **Carpeta de Organización:** Directorio raíz donde el sistema guardará la estructura interna de imágenes (covers de volúmenes, logos, etc.) descargadas de internet.

### **Directorios del Sistema**
Rutas donde BabelComics4 almacena su lógica interna:
* **Directorio de datos:** Ubicación del archivo de base de datos (`.db`).
* **Directorio de thumbnails:** Ruta específica para almacenar las miniaturas generadas de tus archivos locales (CBZ/CBR).

### **Directorios de Escaneo**
Gestión de las ubicaciones donde guardas tus cómics.
* **Agregar directorio:** Permite seleccionar nuevas carpetas (discos locales, externos o de red) para que el sistema las vigile.
* **Escanear (Botón Azul):** Inicia la búsqueda manual de nuevos archivos en las rutas configuradas.
* **Lista de carpetas:** Muestra las rutas activas (ej. `/mnt/Green/Comics/...`). Permite eliminar una ruta de la biblioteca usando el icono de **papelera** (rojo).

### **Interfaz**
Personalización visual y de comportamiento:
* **Tema:** Alterna entre modo Claro y Oscuro (integración GTK4).
* **Tamaño de thumbnails:** Ajusta el tamaño en píxeles de las portadas en la grilla principal.
* **Items por lote:** Controla cuántos cómics se cargan en memoria por bloque en el scroll infinito (ej. 20 items).
* **Sensibilidad y Cooldown de scroll:**
    * *Sensibilidad:* Umbral de movimiento necesario para cargar más contenido.
    * *Cooldown:* Milisegundos de espera entre cargas, vital para evitar "saltos" bruscos si se hace scroll muy rápido.

---

## 2. Pestaña Avanzada

Esta sección contiene herramientas técnicas para el mantenimiento de la base de datos, la gestión de memoria y la limpieza de archivos temporales.

![Pestaña de Configuración Avanzada](Imagenes/configuracion_avanzada.png)

### **Base de Datos**
Herramientas para la gestión del archivo SQLite (`babelcomics.db`):
* **Selector de archivo:** Muestra la ruta y el tamaño actual de la DB.
* **Crear Backup:** Genera una copia de seguridad instantánea de toda tu catalogación.
* **Optimizar (VACUUM):** Ejecuta un proceso de mantenimiento interno para desfragmentar la base de datos y recuperar espacio en disco, mejorando la velocidad de las consultas.

### **Rendimiento**
Ajustes para aprovechar el hardware de tu equipo:
* **Workers concurrentes:** Número de hilos (threads) simultáneos para tareas pesadas (descargas, escaneos).
    * *Nota:* Un valor más alto (ej. 8) acelera los procesos pero consume más CPU.
* **Cache de thumbnails:** Switch para mantener las miniaturas en memoria RAM, agilizando la navegación.
* **Limpieza automática:** Si está activo, el sistema eliminará archivos temporales innecesarios al cerrar la aplicación.

### **Thumbnails (Mantenimiento de Imágenes)**
Gestión del almacenamiento de portadas:
* **Regenerar Covers de Volúmenes:** Fuerza la re-descarga de todas las portadas de series desde ComicVine (útil si hay imágenes rotas o desactualizadas).
* **Limpiar Cache de Thumbnails:** Borra físicamente todas las miniaturas generadas para liberar espacio en disco.
* **Estadísticas:** Muestra un resumen en tiempo real de cuántos covers hay almacenados y cuánto espacio ocupan (ej. *1066 covers, 228.8 MB*). El botón de **refrescar** actualiza este dato.