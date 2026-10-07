# Target Architecture

```text
                         USER
                          |
                    UI5 / OpenUI5
                          |
                          v
                  ASP.NET Core BFF/API
                   /               \
                  /                 \
                 v                   v
       SAP B1 Service Layer       HANA DEV
       technical integration      READ ONLY
              user
                 |
                 v
        SAP Business One 10 HANA
```

## Engineering Agent

```text
ChatGPT / Engineer
       |
       v
SAP B1 Engineering Copilot (Python)
       |
       +-- Skills
       |    +-- sap-legacy-modernizer
       |    +-- ui5-premium-crafter
       |    +-- crystal-runtime-guardian
       |    +-- hana-report-optimizer
       |    +-- sl-model-generator
       |    +-- sap-test-engineer
       |
       +-- Local Tools
            +-- filesystem
            +-- git / GitHub
            +-- dotnet
            +-- python
            +-- npm / UI5
            +-- Service Layer DEV
            +-- HANA DEV read-only
            +-- SAP official documentation
```

## Pending Technical Spike
AUTH-001: validar el mecanismo soportado para autenticar usuarios finales con sus credenciales SAP Business One mientras las operaciones Service Layer se ejecutan mediante el único usuario técnico de integración. No implementar lectura de hashes/contraseñas desde tablas HANA.
