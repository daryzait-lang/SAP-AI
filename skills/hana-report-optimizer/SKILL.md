---
name: hana-report-optimizer
description: Analiza y optimiza SQL HANA para SAP Business One y fuentes de reporting.
---
# Reglas
- Trabajar contra HANA DEV en modo solo lectura.
- Usar sintaxis SAP HANA.
- No inventar tablas/campos/UDF.
- Revisar joins, cardinalidad, filtros, agregaciones y funciones.
- Preservar semántica del reporte.
- Explicar cambios de rendimiento.
- Para Crystal Reports, considerar parámetros, command objects, subreportes y datasets.
- Prohibido DML/DDL salvo análisis textual explícito.
