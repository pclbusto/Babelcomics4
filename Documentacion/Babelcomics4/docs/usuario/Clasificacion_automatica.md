# Proceso de Categorización Automática

La categorización automática utiliza inteligencia artificial para identificar y asignar la categoría correspondiente a cada problema (“issue”) dentro de un volumen. Este proceso se apoya en información previamente registrada y en un mecanismo de análisis automático basado en vectores de características.

---

## 1. Requisitos Previos

Antes de ejecutar la clasificación automática, deben estar cargados en el sistema los valores de referencia que se utilizan para comparar y reconocer los distintos tipos de problemas o crisis.  
Estos valores funcionan como base para que el sistema pueda determinar similitudes y realizar la categorización final.

---

## 2. Proceso de Medición

El proceso de medición analiza cada problema del volumen y genera una representación numérica llamada *vector de características*.

### 2.1. Cálculo del vector

Para cada issue, el sistema calcula un vector que resume sus características principales.  
Este vector será utilizado más adelante para comparar el contenido con otros elementos ya registrados.

### 2.2. Envío al proceso de captura

Una vez que el vector está generado, se envía automáticamente al proceso de captura, que incluye los módulos de Inteligencia Artificial y Microcomputing.  
Estos módulos procesan la información y preparan el contenido para la siguiente etapa del flujo.

---

## 3. Embedding y Comparación

El sistema utiliza técnicas de embeddings para representar cada cover (portada) dentro de un espacio multidimensional.

### 3.1. Generación automática de embeddings

El cálculo de embeddings se ejecuta de forma automática en los siguientes casos:

- Cuando se descarga un volumen completo.
- Cuando se descargan o se preparan covers para subir un volumen al sistema.

En estos escenarios, el sistema genera y actualiza los embeddings sin requerir acciones adicionales por parte del usuario.

### 3.2. Reejecución y recuperación del proceso de embedding

En situaciones excepcionales, pueden ocurrir problemas con la información asociada a los embeddings.  
Por ejemplo:

- Se borró la columna de embeddings en la base de datos.
- Se realizaron modificaciones manuales sobre la base de datos.
- Se habilitó la creación manual de códigos u otros datos vinculados a los issues o covers.

En estos casos, el sistema permite ejecutar nuevamente el proceso de embedding de forma más rápida, utilizando el mismo mecanismo descrito en este capítulo.  
Esta reejecución sirve como herramienta de recuperación para restablecer los vectores de características y volver a habilitar la categorización automática.

> **Importante:**  
> Si la información de base fue alterada manualmente (por ejemplo, códigos creados o ajustados a mano, datos incompletos o no alineados con el contenido real del volumen), la “firma digital” generada por el embedding puede no ser plenamente representativa del problema o de la portada.  
> Como consecuencia, los resultados de similitud y categorización podrían ser menos precisos.

### 3.3. Búsqueda de similitud

Una vez calculados los embeddings, el sistema compara el embedding recién generado con los embeddings almacenados.  
La categorización automática selecciona como resultado la coincidencia cuya distancia sea la menor dentro del espacio vectorial.  
En otras palabras, el sistema determina cuál es el elemento más similar según sus características numéricas.

---

## 4. Resultado Final

Una vez identificada la coincidencia más cercana, el sistema asigna la categoría correspondiente al issue evaluado.  
Este proceso se ejecuta de forma completamente automática y no requiere intervención del usuario, más allá de iniciar la operación o, en casos especiales, forzar la reejecución del proceso de embedding cuando haya habido modificaciones o problemas en la base de datos.
