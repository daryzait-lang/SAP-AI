# SAP B1 Engineering Copilot — Blueprint

Arquitectura recomendada: 1 agente principal + Skills especializadas + Tools locales controladas.

## Agente principal
`sap-b1-engineering-copilot`

Responsabilidad:
- Orquestar análisis, migración, generación, pruebas y entrega.
- Mantener el contexto técnico del proyecto.
- Invocar Skills especializadas.
- Usar herramientas locales con políticas de aprobación.
- Trabajar siempre en ramas Git y abrir Pull Requests.
- No hacer merge automáticamente.

## Skills iniciales
1. sap-legacy-modernizer
2. ui5-premium-crafter
3. crystal-runtime-guardian
4. hana-report-optimizer
5. sl-model-generator
6. sap-test-engineer

## Arquitectura destino
UI5/OpenUI5 -> ASP.NET Core -> SAP Business One Service Layer
                               -> HANA DEV (solo lectura)

## Plataforma
- SAP Business One 10.0 for SAP HANA
- 10.00.130 FP 2008 HOTFIX1 64-bit
- Legacy: VB.NET + .NET Framework 4.7.2 + UI API/DI API
- Target: C# + ASP.NET Core + .NET moderno + Service Layer + UI5
- Deploy: Windows Server + IIS
- Orquestación IA: Python
- Repositorio: GitHub

## Bootstrap Python (CLI y Herramientas Locales)

Base de ingeniería inicial desarrollada en Python estándar (compatible con Python 3.12+, sin dependencias externas requeridas para el bootstrap):

### Comandos disponibles:
```powershell
python -m sap_b1_copilot.cli status
python -m sap_b1_copilot.cli skills
python -m sap_b1_copilot.cli policy
```

### Ejecución de pruebas unitarias:
```powershell
python -m unittest discover tests
```
