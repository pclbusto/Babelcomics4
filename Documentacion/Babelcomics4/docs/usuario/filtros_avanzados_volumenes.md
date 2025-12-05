# Filtros Avanzados para Volúmenes

Esta herramienta permite explorar la base de datos de metadata descargada desde Comic Vine, filtrando las series por fechas, longitud, estado de completitud y editorial.

![Ventana de Filtros Avanzados para Volúmenes](Imagenes/filtro_avanzado_volumen.png)

## 1. Barra de Acciones Superior

Ubicada en la parte superior del panel, gestiona la aplicación de los criterios seleccionados.

* **Cancelar:** Descarta los cambios y cierra el panel.
* **Limpiar:** Reinicia todos los contadores y selectores a sus valores por defecto.
* **Aplicar:** (Botón Azul) Ejecuta el filtro y refresca la lista de volúmenes en la ventana principal.

## 2. Criterios de Filtrado

### **Año de Publicación**
Define un intervalo de tiempo para localizar series publicadas en una época específica.
* **Controles:** Selectores numéricos para establecer el rango.
    * **Año mínimo:** Inicio del rango (ej. 1900).
    * **Año máximo:** Fin del rango (ej. 2030).

### **Cantidad de Números**
Filtra los volúmenes según su longitud o duración total.
* **Controles:** Selectores de cantidad mínima y máxima de *issues*.
* **Uso:** Útil para diferenciar tipos de series:
    * *Miniseries:* Configurar un rango bajo (Ej: 1 a 6 números).
    * *Series Regulares:* Configurar rangos altos (Ej: más de 50 números).

### **Estado de Colección**
Permite filtrar según el nivel de completitud de la serie en tu biblioteca local (la relación entre los *issues* que existen en Comic Vine y los archivos que tú tienes descargados).
* **Control:** Lista desplegable.
* **Opción visible:** "Todos los volúmenes".
* **Otras opciones probables:** "Completos" (tienes todos los números) o "Incompletos" (te falta alguno).

### **Editorial**
Permite restringir la búsqueda a una casa editorial específica.
* **Control:** Campo de selección con ícono de lápiz.
* **Funcionamiento:** Al hacer clic en el ícono de edición (lápiz), se abre un selector para elegir la editorial deseada (ej. Marvel, DC, Image), filtrando la lista de volúmenes para mostrar exclusivamente las series publicadas por ella.