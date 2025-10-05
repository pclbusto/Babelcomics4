# Sistema de Búsqueda Avanzada - Ejemplos de Uso

## Nuevo Sistema de Filtros Contextuales

### ✅ **Problema Resuelto**
- **Antes**: Una sola search bar compartida entre todas las vistas
- **Ahora**: Cada vista (Comics, Volúmenes, Editoriales) mantiene su propio estado de búsqueda independiente

## Ejemplos de Búsqueda Avanzada para Comics

### Búsqueda con Múltiples Términos (Operador +)

#### Ejemplo 1: `Superman+2015`
- **Busca**: Comics que contengan TANTO "Superman" COMO "2015" en el nombre del archivo
- **Resultado**: Archivos como "Superman Vol 4 #41 (2015).cbr" o "Action Comics Superman 2015 Annual.cbz"
- **Excluye**: "Superman Vol 3 #52 (2011).cbr" (no tiene 2015)

#### Ejemplo 2: `Batman+Detective+2016`
- **Busca**: Comics con "Batman", "Detective" Y "2016"
- **Resultado**: "Detective Comics Batman 2016 #934.cbr"
- **Excluye**: "Batman 2016 #1.cbr" (falta "Detective")

#### Ejemplo 3: `Wonder+Woman+600`
- **Busca**: Comics con "Wonder", "Woman" y "600"
- **Resultado**: "Wonder Woman Vol 1 #600.cbr"

### Búsqueda Simple (Sin +)

#### Ejemplo: `Superman`
- **Busca**: Cualquier comic que contenga "Superman" en el nombre
- **Resultado**: Todos los comics de Superman independientemente del año

## Estados Independientes por Vista

### Comics: `Superman+2015`
- Solo muestra comics físicos con Superman de 2015
- No afecta otras vistas

### Volúmenes: `Batman`
- Solo muestra volúmenes de Batman
- Independiente de la búsqueda de comics

### Editoriales: `DC`
- Solo muestra editorial DC Comics
- No interfiere con búsquedas anteriores

## Comportamiento Inteligente

### ✅ **Filtros Contextuales**
- **Comics**: Busca en nombres de archivos, soporta años y números
- **Volúmenes**: Busca en nombres de volúmenes
- **Editoriales**: Busca en nombres de editoriales

### ✅ **Persistencia de Estado**
- Al cambiar de Comics → Volúmenes → Comics, mantiene "Superman+2015"
- Cada vista recuerda su última búsqueda

### ✅ **Placeholders Informativos**
- Comics: "Buscar comics (ej: Superman+2015)..."
- Volúmenes: "Buscar volúmenes..."
- Editoriales: "Buscar editoriales..."

## Casos de Uso Comunes

### Coleccionista Organizado
```
Comics: "X-Men+2019"        → Solo X-Men del año 2019
Volúmenes: "X-Men"          → Todos los volúmenes de X-Men
Comics: "Spider-Man+Ultimate" → Solo Spider-Man Ultimate
```

### Búsqueda por Saga
```
Comics: "Civil+War+2006"    → Civil War original
Comics: "Civil+War+2016"    → Civil War II
Comics: "Secret+Wars+2015"  → Secret Wars reciente
```

### Búsqueda por Número Específico
```
Comics: "Batman+700"        → Batman #700 (especial)
Comics: "Action+1000"       → Action Comics #1000
Comics: "Detective+1000"    → Detective Comics #1000
```

## Beneficios

1. **Sin Interferencia**: Buscar en comics no afecta la vista de volúmenes
2. **Búsquedas Complejas**: Múltiples criterios con operador +
3. **Memoria de Estado**: Cada vista recuerda su búsqueda
4. **Contexto Inteligente**: Filtros específicos para cada tipo de contenido
5. **Experiencia Fluida**: Cambiar entre vistas mantiene el contexto de trabajo

## Implementación Técnica

- **Estados Independientes**: `self.search_states` por vista
- **Filtros Avanzados**: Soporte para `filtrar_año_o_numero()`
- **Operador AND**: Todos los términos separados por + deben coincidir
- **Fallback Inteligente**: Si falla búsqueda avanzada, usa búsqueda simple