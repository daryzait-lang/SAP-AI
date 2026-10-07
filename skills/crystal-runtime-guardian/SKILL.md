---
name: crystal-runtime-guardian
description: Protege la compatibilidad entre SAP Business One y Crystal Reports Runtime y adapta reportes existentes.
---
# Perfil base conocido
- SAP Business One 10.00.130 FP 2008 HOTFIX1 64-bit.
- CR for SAP Business One observado: 14.2.8.3426.
- Runtime existente observado: 13.0.25.3158.
- AddOn legacy actualmente instala Runtime 13.0.40.

# Objetivo
Evitar que el instalador o las referencias del AddOn dañen el funcionamiento de Crystal Reports de SAP B1.

# Procedimiento
1. Detectar runtime instalado.
2. Inspeccionar referencias CrystalDecisions.*.
3. Revisar x86/x64, Copy Local, app.config y paquetes.
4. Revisar instalador y prerequisitos.
5. Comparar con documentación oficial aplicable al FP/PL exacto.
6. Bloquear recomendaciones de upgrade/reemplazo sin compatibilidad demostrada.
7. Adaptar consultas/fuentes HANA conservando el reporte cuando sea viable.
