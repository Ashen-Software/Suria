Plan de Implementación por Hitos
--------------------------------

### Hito 1: Infraestructura Base

*   Configuración de repositorio y GitHub Actions
    
*   Esquema de base de datos en Supabase
    
*   Sistema de logging básico
    

### Hito 2: Detección de Cambios

*   Scrapers livianos para las fuentes:
    - ANH (API Socrata)
    - UPME (Proyecciones: Gas, Electricidad, Potencia, Capacidad)
    - MinMinas (Declaración de Producción)
    
*   Lógica de comparación y trigger
    
*   Configuración de alertas básicas
    

### Hito 3: ETL Completo

*   Contenedor Playwright + dependencias
    
*   Pipelines de transformación por fuente
    
*   Mecanismos de carga y UPSERT
    
*   Esquemas SQL modulares por métrica
    

### Hito 4: Dashboard

*   Aplicación React base
    
*   Visualizaciones principales
    
*   Despliegue en DigitalOcean/Coolify
    

### Hito 5: Monitorización Avanzada

*   Dashboards de métricas ETL
    
*   Alertas proactivas
    
*   Documentación operativa
