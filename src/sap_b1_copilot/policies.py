"""Políticas centrales de ejecución y seguridad para SAP B1 Engineering Copilot.

Derivadas de AGENTS.md y policies/SECURITY.md.
Centraliza las reglas para:
- Comandos permitidos sin aprobación
- Comandos que requieren aprobación humana
- Operaciones prohibidas por defecto
- Protección estricta de producción
- HANA DEV solo lectura (read-only)
- Prohibición de merge automático
- Prohibición de push directo a main
- Detección y sanitización de secretos
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class PolicyDecision(str, Enum):
    """Decisión de política de ejecución."""

    ALLOWED = "ALLOWED"  # Permitido sin aprobación adicional dentro del workspace
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"  # Requiere aprobación humana previa
    FORBIDDEN = "FORBIDDEN"  # Estrictamente prohibido por defecto


@dataclass(frozen=True)
class PolicyResult:
    """Resultado de la evaluación de una política."""

    decision: PolicyDecision
    category: str
    reason: str

    @property
    def is_allowed(self) -> bool:
        return self.decision == PolicyDecision.ALLOWED

    @property
    def requires_approval(self) -> bool:
        return self.decision == PolicyDecision.REQUIRES_APPROVAL

    @property
    def is_forbidden(self) -> bool:
        return self.decision == PolicyDecision.FORBIDDEN


# Patrones SQL HANA prohibidos (DML / DDL / mutación)
FORBIDDEN_SQL_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "UPSERT",
    "MERGE",
    "CREATE",
    "ALTER",
    "DROP",
    "TRUNCATE",
    "RENAME",
    "GRANT",
    "REVOKE",
)

# Patrones para comandos permitidos sin aprobación
ALLOWED_COMMAND_PATTERNS = (
    r"^\s*git\s+(status|diff|log|branch|checkout|switch|show)(\s+.*)?$",
    r"^\s*dotnet\s+(restore|build|test)(\s+.*)?$",
    r"^\s*(python|py|python3)\s+.*$",
    r"^\s*npm\s+test(\s+.*)?$",
    r"^\s*npx\s+(ui5|@ui5)(\s+.*)?$",
)

# Patrones de comandos que requieren aprobación humana
APPROVAL_REQUIRED_COMMAND_PATTERNS = (
    (r"\b(choco|winget|pip\s+install|npm\s+install|dotnet\s+tool\s+install)\b", "Instalación de software o paquetes"),
    (r"\b(reg(\.exe)?|Set-ItemProperty.*Registry)\b", "Modificación del Registro de Windows"),
    (r"\b(sc(\.exe)?|net\s+start|net\s+stop|Stop-Service|Start-Service)\b", "Modificación de servicios de Windows"),
    (r"\b(netsh|New-NetFirewallRule)\b", "Modificación de reglas de Firewall"),
    (r"\b(certutil|Import-Certificate)\b", "Modificación o manipulación de certificados"),
    (r"\b(rmdir\s+/s|Remove-Item\s+-Recurse|rm\s+-rf)\b", "Borrado recursivo o masivo de directorios"),
    (r"\bgit\s+push\s+.*(--force|-f)\b", "Git force push"),
    (r"\bgit\s+push\s+.*--delete\b", "Borrado de rama remota en Git"),
    (r"\b(\.msi|\.exe)\b", "Ejecución de instaladores o ejecutables binarios"),
)

# Patrones de secretos conocidos para sanitización y alerta
SECRET_PATTERNS = [
    (r"(?i)(b1session|sessionid|cookie\s*:\s*b1session)\s*[=:]\s*['\"]?([a-zA-Z0-9\-_]+)", "SAP B1SESSION"),
    (r"(?i)(password|pwd|contrase[ñn]a)\s*[=:]\s*['\"]?([^\s'\";]+)", "Password"),
    (r"(?i)(api[_-]?key|secret[_-]?key|token)\s*[=:]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})", "API Key / Token"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{16,}", "Bearer Token"),
]


class PolicyEngine:
    """Motor central de evaluación de políticas según AGENTS.md y SECURITY.md."""

    @staticmethod
    def evaluate_command(command: str) -> PolicyResult:
        """Evalúa un comando de shell según las políticas del proyecto."""
        cmd_clean = command.strip()

        # 1. Chequeo de operaciones git prohibidas explícitas en comando
        if re.search(r"\bgit\s+push\s+([^\s]+\s+)?(main|refs/heads/main)\b", cmd_clean):
            return PolicyResult(
                decision=PolicyDecision.FORBIDDEN,
                category="git_main_protection",
                reason="Prohibido el push directo a la rama 'main' (AGENTS.md / SECURITY.md).",
            )

        if re.search(r"\bgit\s+merge\b", cmd_clean) and "--no-ff" in cmd_clean and "auto" in cmd_clean.lower():
            return PolicyResult(
                decision=PolicyDecision.FORBIDDEN,
                category="git_auto_merge",
                reason="Prohibido el merge automático sin revisión y aprobación humana.",
            )

        # 2. Chequeo de comandos que requieren aprobación humana
        for pattern, desc in APPROVAL_REQUIRED_COMMAND_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                return PolicyResult(
                    decision=PolicyDecision.REQUIRES_APPROVAL,
                    category="human_approval_required",
                    reason=f"Requiere aprobación humana previa: {desc}.",
                )

        # 3. Chequeo de comandos permitidos sin aprobación
        for pattern in ALLOWED_COMMAND_PATTERNS:
            if re.match(pattern, cmd_clean, re.IGNORECASE):
                return PolicyResult(
                    decision=PolicyDecision.ALLOWED,
                    category="allowed_workspace_command",
                    reason="Comando permitido sin aprobación dentro del workspace.",
                )

        # Por defecto cualquier otro comando requiere revisión/aprobación
        return PolicyResult(
            decision=PolicyDecision.REQUIRES_APPROVAL,
            category="unlisted_command",
            reason="Comando no incluido en la lista permitida sin aprobación; requiere confirmación.",
        )

    @staticmethod
    def evaluate_sql(query: str) -> PolicyResult:
        """Evalúa una consulta HANA asegurando la política de SOLO LECTURA (READ-ONLY)."""
        clean_query = query.strip()
        # Normalizar espacios y saltos de línea
        normalized = " ".join(clean_query.split())

        # Remover comentarios SQL simples (-- ...) y bloques (/* ... */)
        query_without_comments = re.sub(r"--.*?(\n|$)", " ", clean_query)
        query_without_comments = re.sub(r"/\*.*?\*/", " ", query_without_comments, flags=re.DOTALL).strip()

        if not query_without_comments:
            return PolicyResult(
                decision=PolicyDecision.FORBIDDEN,
                category="hana_empty_query",
                reason="La consulta SQL está vacía.",
            )

        # Buscar palabras clave prohibidas DML / DDL como tokens individuales
        for keyword in FORBIDDEN_SQL_KEYWORDS:
            if re.search(rf"\b{keyword}\b", query_without_comments, re.IGNORECASE):
                return PolicyResult(
                    decision=PolicyDecision.FORBIDDEN,
                    category="hana_read_only",
                    reason=(
                        f"Operación SQL '{keyword}' prohibida en HANA DEV. "
                        "HANA es estrictamente de SOLO LECTURA (SELECT / análisis no mutante)."
                    ),
                )

        # Verificar si comienza con SELECT o EXPLAIN
        tokens = query_without_comments.split()
        first_token = tokens[0].upper() if tokens else ""

        if first_token in ("SELECT", "EXPLAIN"):
            return PolicyResult(
                decision=PolicyDecision.ALLOWED,
                category="hana_read_only",
                reason=f"Operación {first_token} permitida en HANA DEV en modo solo lectura.",
            )

        return PolicyResult(
            decision=PolicyDecision.FORBIDDEN,
            category="hana_read_only",
            reason=f"Sentencia SQL no reconocida o no permitida: '{first_token}'. Solo se permite SELECT/EXPLAIN.",
        )

    @staticmethod
    def evaluate_git_push(branch: str, force: bool = False) -> PolicyResult:
        """Evalúa una operación git push."""
        clean_branch = branch.strip().lower()

        if clean_branch in ("main", "master", "origin/main", "origin/master"):
            return PolicyResult(
                decision=PolicyDecision.FORBIDDEN,
                category="git_push_main",
                reason="Está estrictamente prohibido hacer push directo a 'main'. Usar ramas 'agent/<tarea>'.",
            )

        if force:
            return PolicyResult(
                decision=PolicyDecision.REQUIRES_APPROVAL,
                category="git_force_push",
                reason="Git force push requiere aprobación humana explícita.",
            )

        return PolicyResult(
            decision=PolicyDecision.ALLOWED,
            category="git_push_branch",
            reason=f"Push permitido a la rama de tarea '{branch}' previa autorización del usuario.",
        )

    @staticmethod
    def evaluate_git_merge(target_branch: str, automated: bool = False) -> PolicyResult:
        """Evalúa una operación git merge."""
        clean_branch = target_branch.strip().lower()

        if automated:
            return PolicyResult(
                decision=PolicyDecision.FORBIDDEN,
                category="git_auto_merge",
                reason="El merge automático está prohibido. Todo merge requiere revisión humana y Pull Request.",
            )

        if clean_branch in ("main", "master"):
            return PolicyResult(
                decision=PolicyDecision.REQUIRES_APPROVAL,
                category="git_merge_main",
                reason="El merge a 'main' requiere Pull Request y aprobación humana.",
            )

        return PolicyResult(
            decision=PolicyDecision.ALLOWED,
            category="git_merge_branch",
            reason=f"Merge a la rama '{target_branch}' permitido con supervisión.",
        )

    @staticmethod
    def evaluate_production_access(target_env: str, approved: bool = False) -> PolicyResult:
        """Evalúa un intento de acceso a entornos de producción."""
        env_upper = target_env.strip().upper()

        if env_upper in ("PROD", "PRODUCTION", "PRD"):
            if not approved:
                return PolicyResult(
                    decision=PolicyDecision.FORBIDDEN,
                    category="production_protection",
                    reason=(
                        "El acceso a producción está completamente fuera de alcance por defecto. "
                        "Requiere política específica y aprobación humana explícita."
                    ),
                )
            return PolicyResult(
                decision=PolicyDecision.REQUIRES_APPROVAL,
                category="production_protection",
                reason="Operación en producción aprobada bajo supervisión estricta.",
            )

        return PolicyResult(
            decision=PolicyDecision.ALLOWED,
            category="environment_access",
            reason=f"Acceso al entorno '{target_env}' permitido bajo reglas de DEV.",
        )

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitiza texto enmascarando secretos detectados (passwords, tokens, B1SESSION)."""
        sanitized = text
        for pattern, _ in SECRET_PATTERNS:
            def replace_match(m: re.Match) -> str:
                full = m.group(0)
                # Enmascarar la captura secreta
                secret_part = m.group(m.lastindex or 0)
                return full.replace(secret_part, "***REDACTED***")
            sanitized = re.sub(pattern, replace_match, sanitized)
        return sanitized

    @staticmethod
    def detect_potential_secrets(text: str) -> list[str]:
        """Detecta posibles secretos en un texto para alertar antes de persistir o mostrar."""
        findings: list[str] = []
        for pattern, label in SECRET_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                findings.append(f"Detectado posible secreto: {label} ({len(matches)} ocurrencias)")
        return findings

    @classmethod
    def get_policy_summary(cls) -> dict[str, list[str]]:
        """Devuelve un resumen estructurado y centralizado de todas las políticas del proyecto."""
        return {
            "permitido_sin_aprobacion": [
                "git status, git diff, git log, git branch, git checkout/switch para ramas de tarea",
                "dotnet restore, dotnet build, dotnet test",
                "python / py para scripts y herramientas del proyecto",
                "npm test y comandos UI5 de desarrollo locales",
                "Lectura y edición de archivos dentro del workspace autorizado",
                "Consultas HANA DEV con SELECT (modo solo lectura)",
            ],
            "requiere_aprobacion_humana": [
                "Instalar o desinstalar software o paquetes externos",
                "Ejecutar instaladores binarios (.msi, .exe)",
                "Modificar el Registro de Windows, variables PATH o servicios del sistema",
                "Modificar configuración de Firewall o certificados de red",
                "Borrar directorios sustanciales o ramas remotas",
                "Ejecutar git push --force (force push)",
                "Despliegues hacia servidores o cualquier acción sobre producción",
                "Modificar almacenes o bóvedas de credenciales",
                "Cualquier operación destructiva sobre bases de datos",
            ],
            "siempre_prohibido_por_defecto": [
                "Push directo a la rama 'main'",
                "Merge automático (auto-merge)",
                "Operaciones DML/DDL directas en HANA (INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, TRUNCATE)",
                "Escribir directamente en tablas de SAP Business One evadiendo Service Layer",
                "Acceder o conectar a entornos de PRODUCCIÓN sin política y aprobación explícitas",
                "Exponer secretos en código, logs, commits, prompts o documentación",
                "Registrar passwords, tokens o cookies B1SESSION",
                "Leer hashes de contraseñas de HANA o realizar ingeniería inversa de credenciales (AUTH-001)",
            ],
            "hana_read_only": [
                "Acceso permitido únicamente en DEV mediante credencial de solo lectura",
                "Solo sentencias SELECT y EXPLAIN no mutantes",
                "Prohibido INSERT, UPDATE, DELETE, UPSERT, MERGE, DDL y procedimientos mutantes",
            ],
            "proteccion_produccion": [
                "Producción deshabilitada por defecto en la configuración",
                "Prohibido conectar, desplegar o ejecutar comandos sobre producción",
                "Requiere autorización humana explícita y política específica aprobada",
            ],
            "reglas_git": [
                "Nunca modificar main directamente; siempre crear ramas 'agent/<tarea>'",
                "Compilar y ejecutar pruebas antes de confirmar o solicitar Pull Request",
                "Todo cambio a main requiere Pull Request y revisión humana",
                "Nunca usar force push sin aprobación explícita",
            ],
            "manejo_secretos": [
                "Los secretos permanecen exclusivamente en el entorno local (.env / variables)",
                "El archivo real .env nunca debe incluirse en Git (ignorado en .gitignore)",
                "Sanitización automática de B1SESSION, passwords, tokens y connection strings",
                "Si se detecta un secreto en código: no hacer eco, redactar y advertir rotación",
            ],
        }
