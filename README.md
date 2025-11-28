# Suria

**Suria** es un sistema ETL automatizado que extrae, transforma y centraliza datos sobre el gas natural de Colombia (ANH, UPME, MinMinas) en una base de datos PostgreSQL. Mediante schedulers programados, detecta cambios en las fuentes, procesa proyecciones de demanda de gas, electricidad y capacidad instalada, y alimenta dashboards interactivos para análisis del sector energético.

---

Accede a la aplicación: https://suria.software/

Toda la documentación detallada, guías de uso y referencias técnicas se encuentran publicadas en GitHub Pages, generada con MkDocs.

Accede a la documentación completa aquí: [Ver la documentación completa](https://ashen-software.github.io/Suria/)

## Construir la documentación
Los archivos fuente de la documentación se encuentran en la carpeta docs/. Para previsualizar o reconstruir la documentación localmente, usa los siguientes comandos:

- 1. Instalar dependencias: 

```pip install mkdocs mkdocs-material```

- 2. Ejecutar previsualización local:

```mkdocs serve```
