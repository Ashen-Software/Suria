# Schema de Base de Datos para Declaraciones de Gas Natural

Este directorio contiene el schema SQL para crear las tablas en Supabase y scripts para insertar los datos extraídos.

## Estructura del Schema

El schema está diseñado para almacenar la estructura jerárquica completa de las declaraciones:

```
extractions (tabla raíz)
├── declarations
│   ├── resolutions
│   │   └── soporte_magnetico (archivos Excel)
│   ├── cronogramas (opcional)
│   ├── anexos (múltiples)
│   └── acceso_sistema (opcional)
└── plantillas_declaracion
    └── plantillas (OPERADOR/ASOCIADO)
```

## Instalación en Supabase

### 1. Crear las tablas

1. Accede a tu proyecto en Supabase
2. Ve a **SQL Editor**
3. Abre el archivo `schema_supabase.sql`
4. Copia y pega todo el contenido
5. Ejecuta el script

El script creará:
- ✅ 9 tablas principales
- ✅ Índices para optimización
- ✅ Triggers para `updated_at` automático
- ✅ Vistas útiles para consultas
- ✅ Funciones helper

### 2. Verificar la instalación

Ejecuta esta consulta para verificar que todas las tablas se crearon:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'extractions',
    'declarations',
    'resolutions',
    'soporte_magnetico',
    'cronogramas',
    'anexos',
    'acceso_sistema',
    'plantillas_declaracion',
    'plantillas'
)
ORDER BY table_name;
```

## Insertar Datos

### Opción 1: Usando el script Python

```python
from db_insert_example import load_json_and_insert

SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu-service-role-key"
JSON_PATH = "processed/declaracion_20251126_164206.json"

load_json_and_insert(JSON_PATH, SUPABASE_URL, SUPABASE_KEY)
```

**Nota**: Necesitas instalar el cliente de Supabase:
```bash
pip install supabase
```

### Opción 2: Usando la API REST de Supabase

Puedes usar cualquier cliente HTTP para insertar datos usando la API REST de Supabase.

## Consultas Útiles

### Obtener todas las declaraciones de una extracción

```sql
SELECT 
    d.declaration_title,
    d.total_resolutions,
    COUNT(r.id) as resolutions_count
FROM declarations d
JOIN extractions e ON e.id = d.extraction_id
LEFT JOIN resolutions r ON r.declaration_id = d.id
WHERE e.id = 'tu-extraction-id'
GROUP BY d.id, d.declaration_title, d.total_resolutions;
```

### Obtener resoluciones con sus soportes magnéticos

```sql
SELECT * FROM vw_resolutions_with_soportes
WHERE declaration_title LIKE '%2025%';
```

### Obtener resumen de una extracción

```sql
SELECT get_extraction_summary('tu-extraction-id');
```

### Buscar declaraciones por período

```sql
SELECT 
    declaration_title,
    total_resolutions,
    extraction_date
FROM vw_declarations_complete
WHERE declaration_title LIKE '%2025%'
ORDER BY extraction_date DESC;
```

## Estructura de Tablas

### `extractions`
Almacena información de cada ejecución del scraper.

**Campos principales:**
- `id` (UUID): ID único
- `extraction_date`: Fecha de la extracción
- `source_url`: URL fuente
- `total_declarations`: Total de declaraciones encontradas
- `total_plantillas`: Total de grupos de plantillas

### `declarations`
Almacena las declaraciones principales (ej: "Declaración 2025-2034").

**Campos principales:**
- `id` (UUID): ID único
- `extraction_id` (FK): Referencia a extractions
- `declaration_title`: Título completo de la declaración
- `total_resolutions`: Número total de resoluciones

### `resolutions`
Almacena las resoluciones asociadas a cada declaración.

**Campos principales:**
- `id` (UUID): ID único
- `declaration_id` (FK): Referencia a declarations
- `number`: Número de la resolución
- `date`: Fecha de la resolución
- `url`: URL del documento PDF
- `title`: Título completo
- `extracted_data` (JSONB): Datos extraídos del Excel (si se analizó)

### `soporte_magnetico`
Almacena los archivos Excel asociados a resoluciones.

**Campos principales:**
- `id` (UUID): ID único
- `resolution_id` (FK): Referencia a resolutions
- `title`: Título del archivo
- `url`: URL de descarga
- `local_path`: Ruta local (si se descargó)
- `file_size_bytes`: Tamaño en bytes
- `file_size_mb`: Tamaño en MB

### `cronogramas`, `anexos`, `acceso_sistema`
Tablas para metadata adicional de las declaraciones (opcional).

### `plantillas_declaracion` y `plantillas`
Almacenan las plantillas de cargue (OPERADOR/ASOCIADO).

## Seguridad (RLS)

Por defecto, RLS está deshabilitado. Si necesitas habilitar Row Level Security:

1. Descomenta las líneas de `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` en el schema
2. Crea políticas según tus necesidades de acceso

Ejemplo de política pública de lectura:
```sql
CREATE POLICY "Allow public read access" ON public.extractions
    FOR SELECT USING (true);
```

## Mantenimiento

### Actualizar updated_at automáticamente
Los triggers están configurados para actualizar `updated_at` automáticamente en cada UPDATE.

### Índices
Los índices están optimizados para:
- Búsquedas por fecha
- Búsquedas por número de resolución
- Búsquedas por URL
- Búsquedas en JSONB (extracted_data)

### Limpieza de datos antiguos
Puedes crear un script para eliminar extracciones antiguas:

```sql
DELETE FROM extractions 
WHERE extraction_date < NOW() - INTERVAL '1 year';
```

Esto eliminará en cascada todos los registros relacionados gracias a `ON DELETE CASCADE`.

## Troubleshooting

### Error: "relation already exists"
Si una tabla ya existe, usa `CREATE TABLE IF NOT EXISTS` (ya incluido en el schema).

### Error: "duplicate key value"
El schema incluye `UNIQUE` constraints para evitar duplicados. Verifica que no estés intentando insertar datos duplicados.

### Performance
Si tienes muchos datos, considera:
- Particionar tablas por fecha
- Usar índices parciales
- Archivar datos antiguos

## Contacto

Para más información sobre el schema o reportar problemas, revisa la documentación del proyecto.

