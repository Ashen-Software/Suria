# Documentación del Proyecto

Bienvenido a la documentación técnica del proyecto. Aquí encontrarás orientación sobre la arquitectura, la API y el esquema de la base de datos.

## Contenido

- **Arquitectura**: [Diagramas y decisiones de diseño](./arquitectura/overview.md)
- **API**: [Documentación de endpoints](./api/endpoints.md)
- **Base de datos**: [Esquemas y modelos](./database/esquema.md)

## Fuentes de datos

### Regalías por campo (ANH)

Liquidación definitiva de regalías por campo de hidrocarburos desde 2010.

- **Autor:** Agencia Nacional de Hidrocarburos
- **API:** [Socrata — j7js-yk74](https://dev.socrata.com/foundry/www.datos.gov.co/j7js-yk74)

### Declaración de producción (MinMinas)

Producción declarada por productores y comercializadores de gas natural.

- **Autor:** Ministerio de Minas y Energía
- **Formato:** XLSX por periodo
- **Enlace:** [Gas natural — MinMinas](https://www.minenergia.gov.co/es/misional/hidrocarburos/funcionamiento-del-sector/gas-natural/)

### Proyecciones UPME

| Métrica | Unidad | Descripción |
|---------|--------|-------------|
| Demanda Gas Natural | GBTUD | Por categoría (Industrial, Residencial, etc.) |
| Energía Eléctrica | GWh | Por área eléctrica |
| Potencia Máxima | MW | Por área y escenario |
| Capacidad Instalada | MW | Generación Distribuida |

- **Autor:** UPME
- **Formato:** Anexos XLSX
- **Enlace:** [Proyecciones de demanda — UPME](https://www.upme.gov.co/simec/planeacion-energetica/proyeccion_de_demanda/)
