Plan de Implementación por Hitos
--------------------------------

### Hito 1: Infraestructura Base

*   Configuración de repositorio y GitHub Actions
    
*   Esquema de base de datos en Supabase
    
*   Sistema de logging básico
    

### Hito 2: Detección de Cambios

*   Scrapers livianos para las 3 fuentes
    
*   Lógica de comparación y trigger
    
*   Configuración de alertas básicas
    

### Hito 3: ETL Completo

*   Contenedor Playwright + dependencias
    
*   Pipelines de transformación por fuente
    
*   Mecanismos de carga y UPSERT
    

### Hito 4: Dashboard

*   Aplicación Angular base
    
*   Visualizaciones principales
    
*   Despliegue en Vercel/Netlify
    

### Hito 5: Monitorización Avanzada

*   Dashboards de métricas ETL
    
*   Alertas proactivas
    
*   Documentación operativa
    

Estimación de Costos
--------------------

### Capa Gratuita Disponible

*   **GitHub Actions**: ~2,000 minutos/mes (suficiente para uso estimado)
    
*   **Supabase**: 500MB base de datos + 1GB storage (adecuado para inicio)
    
*   **Vercel/Netlify**: Despliegue frontend gratuito
    
*   **Slack**: Webhooks gratuitos para alertas
    

### Puntos de Escalación Futura

*   Supabase Pro: >500MB de datos o >50k filas/mes
    
*   GitHub Actions: >2,000 minutos/mes de procesamiento
    
*   Monitorización: Migración a DataDog si requiere analytics avanzados
    

Runbook Operativo
-----------------

### Procedimientos Comunes

1.  **Ejecución Manual ETL**: Trigger via GitHub UI
    
2.  **Debug de Fallos**: Revisión de logs en GitHub Actions + tabla etl\_logs
    
3.  **Recuperación de Errores**: Re-ejecución con limpieza opcional de datos corruptos
    
4.  **Actualización de Scrapers**: Modificación de selectores ante cambios en fuentes
    

### Métricas de Salud

*   Tiempo de ejecución promedio por fuente
    
*   Tasa de éxito de extracción (>95% objetivo)
    
*   Latencia datos fuente → dashboard (<24 horas)
    
*   Disponibilidad del dashboard (>99.5%)