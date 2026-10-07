# Security and Execution Policy

## Permitido sin aprobación adicional dentro del workspace
- git status/diff/log/branch/checkout
- dotnet restore/build/test
- npm test y comandos UI5 de desarrollo previamente instalados
- python para scripts del proyecto
- lectura/escritura de archivos dentro del workspace autorizado
- consultas HANA SELECT en DEV mediante credencial read-only

## Requiere aprobación humana
- instalar/desinstalar software
- modificar PATH, registro de Windows o servicios
- ejecutar instaladores MSI/EXE
- borrar carpetas o ramas remotas
- force push
- cambios de firewall/certificados
- despliegues a servidores
- acciones sobre producción

## Siempre prohibido por defecto
- push directo a main
- merge automático
- DML/DDL directo en HANA
- exponer secretos
- registrar passwords o B1SESSION
