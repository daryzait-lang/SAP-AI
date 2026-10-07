---
name: sap-legacy-modernizer
description: Moderniza código SAP Business One legacy hacia Service Layer, ASP.NET Core y UI5.
---
# Objetivo
Migrar VB.NET/.NET Framework, UI API y DI API hacia arquitectura web moderna.

# Procedimiento
1. Inventariar formularios, eventos, clases, queries y dependencias SAP.
2. Clasificar cada uso UI API/DI API: UI, lectura, escritura, validación, evento o integración.
3. Extraer reglas de negocio antes de modificar código.
4. Mapear operaciones DI API a Service Layer cuando exista cobertura oficial.
5. Diseñar contratos DTO y servicios backend.
6. Reescribir en C#/.NET moderno; no hacer traducción literal.
7. Delegar UI a `ui5-premium-crafter`.
8. Delegar modelos a `sl-model-generator`.
9. Delegar validación a `sap-test-engineer`.
10. Entregar matriz LEGACY -> TARGET y riesgos.

# Prohibiciones
- No inventar endpoints Service Layer.
- No mover lógica de negocio crítica al navegador.
- No escribir directamente en tablas SAP.
