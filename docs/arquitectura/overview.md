Arquitectura Detallada
----------------------

### 1\. Orquestación y Ejecución (GitHub Actions)

#### Workflows Implementados

**check-updates.yml** (Ejecución Semanal/Mensual)

*   **Trigger:** Cron programado / activación manual
    
*   **Función:** Verifica cambios en fuentes usando Requests + BeautifulSoup
    
*   **Salida:** Dispara ETL completo solo si detecta cambios
    
*   **Costo:** Mínimo (ejecución rápida sin contenedores)
    

**full-etl.yml** (Completo - Solo cuando hay cambios)

*   **Trigger:** Desde check-updates o manual
    
*   **Contenedor:** Playwright + Python para extracción robusta
    
*   **Proceso:** Extracción → Transformación → Carga
    
*   **Costo:** Solo cuando es necesario (2-3 meses)
    

### 2\. Sistema de Logs y Monitorización

#### Estrategia de Logs Multi-nivel

**Nivel 1: Logs Estructurados en GitHub Actions**

*   Logs nativos de ejecución de workflows
    
*   Captura de stdout/stderr de todos los scripts
    
*   Retención automática según política de GitHub

**Nivel 2: Métricas de Performance**

*   Tiempos de ejecución por fuente
    
*   Volumen de datos procesados
    
*   Tasa de éxito/error por componente
    

#### Sistema de Alertas Multi-canal

**1\. GitHub Native Integrations**

*   Notificaciones email nativas sobre fallos de workflows
    
*   Configuración directa en repository settings

**2\. Custom Email Service**
    
*   Notificaciones para stakeholders no técnicos (SMTP gratuito)
    

### 3\. Procesamiento de Datos (ETL)

#### Tecnologías Clave

*   **Python 3.12+**: Lenguaje principal
    
*   **Playwright**: Extracción robusta en sitios complejos
    
*   **Pandas**: Transformación y limpieza de datos
    
*   **BeautifulSoup**: Scraping liviano para detección
    
*   **Supabase Python Client**: Carga eficiente
    

#### Estrategia de Procesamiento

1.  **Extracción Resiliente**: Reintentos automáticos con backoff
    
2.  **Validación en Tiempo Real**: Schemas, rangos, consistencia
    
3.  **Procesamiento Incremental**: Solo datos nuevos/cambiados
    
4.  **Idempotencia**: UPSERTs para evitar duplicados
    

### 4\. Almacenamiento y Backend (Supabase)

#### Esquema de Base de Datos

El sistema utiliza un modelo estrella (star schema) con:

- **Dimensiones compartidas**: `dim_tiempo`, `dim_territorios`, `dim_campos`, `dim_areas_electricas`, `dim_resoluciones`
- **Tablas de hechos**: 
  - `fact_regalias` (ANH)
  - `fact_demanda_gas_natural` (UPME)
  - `fact_energia_electrica` (UPME)
  - `fact_potencia_maxima` (UPME)
  - `fact_capacidad_instalada` (UPME)
  - `fact_oferta_gas` (MinMinas)

Ver [esquema.md](../database/esquema.md) para detalles completos.

#### Optimizaciones para Dashboard

*   Vistas materializadas para consultas frecuentes
    
*   Índices en campos de filtro común (fecha, entidad, territorio)
    
*   Políticas RLS para seguridad de datos
    

### 5\. Frontend y Despliegue

#### Stack Tecnológico

*   **React 19 + Vite + TypeScript**: Aplicación SPA principal
    
*   **Tailwind CSS + DaisyUI**: Estilización, layout y componentes UI
    
*   **Supabase JS Client**: Conexión directa a la base de datos (lectura desde el frontend)
    
*   **TanStack React Query**: Capa de data fetching, caché y paginación incremental (`useInfiniteQuery`)
    
*   **TanStack React Table**: Tablas interactivas con búsqueda y paginación en el navegador
    
*   **Recharts**: Visualizaciones (líneas, áreas, barras, pies) para dashboards energéticos
    
*   **OpenAI Chat Completions API**: Servicio de IA para el chatbot y análisis automáticos del dashboard integrado
    

#### Estrategia de Despliegue

*   **Vite dev server** en local (`npm run dev`), con build estático listo para CD (Vercel/Netlify/DigitalOcean)
    
*   **Variables de Entorno**: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_OPENAI_API_KEY`, `VITE_OPENAI_MODEL`, etc.
    
*   **CDN Global** (según plataforma de despliegue): Distribución optimizada de assets
    

### 6\. Frontend: Páginas y Vistas Clave

*   **Home (`/`)**: Portada y explicación general de Suria.
*   **Integrado (`/integrado`)**: Dashboard que cruza UPME (demanda gas y eléctrica), Declaración MinMinas (`fact_oferta_gas`) y regalías ANH (`fact_regalias`), con:
    * KPIs integrados (demanda total gas, demanda eléctrica, oferta gas, regalías acumuladas).
    * Reconciliación oferta vs demanda de gas (series anuales agregadas).
    * Serie de regalías anuales.
    * Tabla integrada por año con demanda gas, oferta gas, brecha, demanda eléctrica y regalías.
    * Botón **“Generar análisis con IA”** que llama al servicio de LLM y genera un resumen ejecutivo basado en los datos cargados.
*   **Declaración de Gas (`/declaracion-gas`)** y **Regalías (`/regalias`)**: Dashboards detallados por fuente, con visualizaciones, estadísticas y tabla granular.
*   **UPME (`/upme`)**: Página de entrada a los módulos de demanda de gas natural, energía eléctrica, potencia máxima y capacidad instalada.
*   **Dimensiones (`/dimensiones`)**: Catálogo maestro de `dim_tiempo`, `dim_territorios` y áreas eléctricas.

Todas las vistas que consumen tablas de hechos grandes (`fact_oferta_gas`, `fact_regalias`, `fact_demanda_gas_natural`, `fact_energia_electrica`, `fact_potencia_maxima`, `fact_capacidad_instalada`) siguen un mismo patrón:

1. **Servicios Supabase paginados** (`getPage(from, to)` con `.range`) para evitar `statement timeout` en consultas muy grandes.
2. **Capa de helpers** (`loadXPage(page, pageSize)`) que reciben un índice de página y tamaño de página API (por defecto 5000 filas).
3. **`useInfiniteQuery` en el frontend** para traer páginas sucesivas y construir un `flatData` acumulado sobre el que se calculan gráficos, KPIs y tablas.
4. **Carga progresiva y skeletons**: el usuario empieza a ver estructura y primeros datos mientras siguen llegando páginas adicionales en background.

Este patrón está aplicado tanto en los módulos de Declaración/Regalías como en todos los módulos UPME.

[![Diagrama de arquitectura](../assets/diagrams/arquitectura.svg)](../assets/diagrams/arquitectura.svg)
