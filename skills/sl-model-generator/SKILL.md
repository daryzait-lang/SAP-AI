---
name: sl-model-generator
description: Genera modelos tipados a partir de contratos y respuestas JSON de SAP Business One Service Layer.
---
# Salidas
- C# records/classes/DTOs para ASP.NET Core.
- Python Pydantic cuando se necesite tooling.

# Reglas
- Diferenciar entidades SAP de DTOs públicos.
- Tratar nullability explícitamente.
- No asumir campos ausentes.
- Preparar serialización/deserialización consistente.
- Mantener contratos pequeños y orientados al caso de uso.
