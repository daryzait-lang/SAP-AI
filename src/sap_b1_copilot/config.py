"""Configuración central para SAP B1 Engineering Copilot.

Carga configuración operativa sin almacenar ni exponer secretos.
Diferencia entornos (DEV / PROD) y mantiene producción deshabilitada por defecto.
Usa exclusivamente la biblioteca estándar de Python.
"""

from __future__ import annotations

import os
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


class ConfigurationError(Exception):
    """Excepción para errores de configuración."""


class ProductionAccessBlockedError(ConfigurationError):
    """Excepción lanzada cuando se intenta operar en producción estando deshabilitada."""


def _find_project_root() -> Path:
    """Encuentra la raíz del proyecto basándose en la ubicación de este archivo."""
    # src/sap_b1_copilot/config.py -> parents[2] es la raíz del repositorio
    file_path = Path(__file__).resolve()
    # Si estamos en src/sap_b1_copilot/config.py
    candidate = file_path.parent.parent.parent
    if (candidate / "AGENTS.md").is_file() or (candidate / "skills").is_dir():
        return candidate
    # Fallback al directorio de trabajo actual
    cwd = Path.cwd()
    if (cwd / "AGENTS.md").is_file() or (cwd / "skills").is_dir():
        return cwd
    return candidate


def _parse_simple_yaml(content: str) -> dict[str, Any]:
    """Parser liviano para archivos YAML simples usando solo la biblioteca estándar.

    Soporta pares clave-valor simples, anidados por indentación (2 espacios),
    booleanos, números, listas sencillas y comentarios (#).
    """
    result: dict[str, Any] = {}
    current_section: Optional[str] = None
    dedented = textwrap.dedent(content)

    for raw_line in dedented.splitlines():
        # Remover comentarios
        line = re.sub(r"#.*$", "", raw_line).rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if ":" not in stripped:
            continue

        key, val = stripped.split(":", 1)
        key = key.strip()
        val = val.strip()

        def parse_value(v: str) -> Any:
            if not v:
                return None
            if v.lower() in ("true", "yes", "on"):
                return True
            if v.lower() in ("false", "no", "off"):
                return False
            if v.isdigit():
                return int(v)
            try:
                return float(v)
            except ValueError:
                pass
            # Quitar comillas si las tiene
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                return v[1:-1]
            return v

        if indent == 0:
            if not val:
                current_section = key
                result[current_section] = {}
            else:
                current_section = None
                result[key] = parse_value(val)
        elif indent > 0 and current_section is not None:
            if isinstance(result[current_section], dict):
                result[current_section][key] = parse_value(val)

    return result


@dataclass(frozen=True)
class AppConfig:
    """Configuración inmutable de SAP B1 Engineering Copilot.

    No almacena secretos. Proporciona métodos seguros de inspección y rutas.
    """

    project_name: str
    environment: str
    allow_production: bool
    hana_read_only: bool
    project_root: Path

    def is_production(self) -> bool:
        """Indica si el entorno configurado corresponde a producción."""
        return self.environment.strip().upper() == "PROD"

    def is_production_allowed(self) -> bool:
        """Indica si las operaciones en producción están explícitamente habilitadas."""
        return self.allow_production is True

    def get_path(self, relative_path: str | Path) -> Path:
        """Resuelve una ruta relativa con respecto a la raíz del proyecto."""
        return (self.project_root / relative_path).resolve()

    def get_skills_dir(self) -> Path:
        """Devuelve la ruta al directorio de Skills."""
        return self.get_path("skills")

    def get_config_dir(self) -> Path:
        """Devuelve la ruta al directorio de configuración."""
        return self.get_path("config")

    def get_policies_dir(self) -> Path:
        """Devuelve la ruta al directorio de políticas."""
        return self.get_path("policies")

    def get_docs_dir(self) -> Path:
        """Devuelve la ruta al directorio de documentación."""
        return self.get_path("docs")

    def get_src_dir(self) -> Path:
        """Devuelve la ruta al directorio de código fuente."""
        return self.get_path("src")

    def get_tests_dir(self) -> Path:
        """Devuelve la ruta al directorio de pruebas."""
        return self.get_path("tests")

    def safe_summary(self) -> dict[str, Any]:
        """Devuelve un diccionario seguro garantizado sin secretos."""
        return {
            "project_name": self.project_name,
            "environment": self.environment,
            "is_production": self.is_production(),
            "allow_production": self.allow_production,
            "hana_read_only": self.hana_read_only,
            "project_root": str(self.project_root),
            "skills_dir": str(self.get_skills_dir()),
        }

    def __repr__(self) -> str:
        """Representación segura en string sin secretos."""
        return (
            f"AppConfig(project_name={self.project_name!r}, "
            f"environment={self.environment!r}, "
            f"allow_production={self.allow_production!r}, "
            f"hana_read_only={self.hana_read_only!r}, "
            f"project_root={str(self.project_root)!r})"
        )


def load_config(
    config_file: Optional[Path] = None,
    environ: Optional[dict[str, str]] = None,
    project_root: Optional[Path] = None,
) -> AppConfig:
    """Carga la configuración sin incluir secretos.

    Prioridad:
    1. Variables de entorno seguras (SAP_COPILOT_ENV, SAP_ALLOW_PRODUCTION).
    2. Archivo de configuración proporcionado o settings.example.yaml / project_profile.yaml.
    3. Valores por defecto seguros (DEV, producción deshabilitada, HANA read-only).
    """
    env_vars = os.environ if environ is None else environ
    root = (project_root or _find_project_root()).resolve()

    # Valores por defecto seguros
    project_name = "SAP B1 Engineering Copilot"
    environment = "DEV"
    allow_production = False
    hana_read_only = True

    # Intentar cargar desde archivo si existe
    target_file = config_file
    if target_file is None:
        possible_files = [
            root / "config" / "settings.yaml",
            root / "config" / "settings.example.yaml",
            root / "config" / "project_profile.yaml",
        ]
        for f in possible_files:
            if f.is_file():
                target_file = f
                break

    if target_file is not None and target_file.is_file():
        try:
            content = target_file.read_text(encoding="utf-8")
            parsed = _parse_simple_yaml(content)
            if "project" in parsed and isinstance(parsed["project"], dict):
                project_name = parsed["project"].get("name", project_name)
            elif "project_name" in parsed:
                project_name = parsed.get("project_name", project_name)

            if "environment" in parsed and isinstance(parsed["environment"], str):
                environment = parsed["environment"]

            if "allow_production" in parsed:
                allow_production = bool(parsed["allow_production"])

            if "sap" in parsed and isinstance(parsed["sap"], dict):
                if "hana_read_only" in parsed["sap"]:
                    hana_read_only = bool(parsed["sap"]["hana_read_only"])
        except Exception:
            # En caso de error de lectura, se mantienen los valores por defecto seguros
            pass

    # Variables de entorno tienen prioridad sobre el archivo para flags operativas
    env_name = env_vars.get("SAP_COPILOT_ENV") or env_vars.get("ENVIRONMENT")
    if env_name:
        environment = env_name.strip().upper()

    # Producción siempre requiere flag explícita y afirmativa
    allow_prod_var = env_vars.get("SAP_ALLOW_PRODUCTION", "")
    if allow_prod_var.strip().lower() in ("true", "1", "yes"):
        allow_production = True
    elif allow_prod_var.strip().lower() in ("false", "0", "no"):
        allow_production = False
    # Por defecto, la política de AGENTS.md exige que producción esté deshabilitada
    if not allow_prod_var and "allow_production" not in (locals() if target_file else {}):
        allow_production = False

    return AppConfig(
        project_name=project_name,
        environment=environment,
        allow_production=allow_production,
        hana_read_only=hana_read_only,
        project_root=root,
    )
