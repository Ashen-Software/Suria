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

*   **Angular 16+**: Framework principal
    
*   **Tailwind CSS**: Estilización y responsive design
    
*   **Supabase JS Client**: Conexión directa a datos
    
*   **Chart.js/NGX-Charts**: Visualizaciones de datos
    

#### Estrategia de Despliegue

*   **Vercel/Netlify**: Despliegue continuo desde main branch
    
*   **Variables de Entorno**: Configuración segura de endpoints
    
*   **CDN Global**: Distribución optimizada de assets

[![Diagrama de arquitectura](../assets/diagrams/arquitectura.svg)](../assets/diagrams/arquitectura.svg)
