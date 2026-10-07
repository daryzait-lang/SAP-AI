"""CLI inicial para SAP B1 Engineering Copilot.

Comandos disponibles:
- python -m sap_b1_copilot.cli status
- python -m sap_b1_copilot.cli skills
- python -m sap_b1_copilot.cli policy
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Asegurar encoding UTF-8 en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if __package__ is None or __package__ == "":
    # Ejecutado directamente como script (python src/sap_b1_copilot/cli.py)
    _src_dir = Path(__file__).resolve().parent.parent
    if str(_src_dir) not in sys.path:
        sys.path.insert(0, str(_src_dir))
    from sap_b1_copilot.config import load_config
    from sap_b1_copilot.policies import PolicyEngine
    from sap_b1_copilot.skill_registry import SkillRegistry
else:
    # Ejecutado como módulo (python -m sap_b1_copilot.cli)
    from .config import load_config
    from .policies import PolicyEngine
    from .skill_registry import SkillRegistry


def _get_current_git_branch(project_root: Path) -> Optional[str]:
    """Determina la rama actual de Git de manera segura y sin efectos secundarios."""
    # 1. Intentar lectura directa y segura de .git/HEAD
    git_head_file = project_root / ".git" / "HEAD"
    if git_head_file.is_file():
        try:
            head_content = git_head_file.read_text(encoding="utf-8").strip()
            if head_content.startswith("ref: refs/heads/"):
                return head_content.replace("ref: refs/heads/", "").strip()
            # Si es un commit detached
            if len(head_content) == 40:
                return f"detached at {head_content[:8]}"
        except Exception:
            pass

    # 2. Fallback seguro a comando git de solo lectura
    try:
        proc = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception:
        pass

    return "No determinada"


def cmd_status() -> int:
    """Muestra el estado operativo del proyecto."""
    config = load_config()
    registry = SkillRegistry(config.get_skills_dir())
    git_branch = _get_current_git_branch(config.project_root)

    prod_status = (
        "HABILITADA (ADVERTENCIA: Requiere autorización explícita)"
        if config.is_production_allowed()
        else "Deshabilitada (bloqueada por defecto)"
    )

    hana_status = "Solo lectura activa (READ-ONLY)" if config.hana_read_only else "Lectura/Escritura (NO PERMITIDO)"

    print("=" * 60)
    print(" SAP B1 ENGINEERING COPILOT — ESTADO")
    print("=" * 60)
    print(f" Proyecto               : {config.project_name}")
    print(f" Ambiente               : {config.environment}")
    print(f" Producción habilitada  : {prod_status}")
    print(f" HANA DEV Mode          : {hana_status}")
    print(f" Skills encontradas     : {registry.count()}")
    print(f" Rama Git actual        : {git_branch}")
    print(f" Raíz del proyecto      : {config.project_root}")
    print("=" * 60)
    return 0


def cmd_skills() -> int:
    """Lista las Skills registradas y válidas en el proyecto."""
    config = load_config()
    registry = SkillRegistry(config.get_skills_dir())
    skills = registry.list_skills()

    print("=" * 60)
    print(f" SKILLS DISPONIBLES ({len(skills)})")
    print("=" * 60)

    if not skills:
        print(" No se encontraron Skills válidas en /skills.")
        return 0

    for idx, skill in enumerate(skills, 1):
        rel_path = skill.path.relative_to(config.project_root) if skill.path.is_relative_to(config.project_root) else skill.path
        rel_file = skill.skill_file.relative_to(config.project_root) if skill.skill_file.is_relative_to(config.project_root) else skill.skill_file
        print(f"[{idx}] {skill.name}")
        print(f"    Ruta        : {rel_path}")
        print(f"    Archivo     : {rel_file}")
        if skill.description:
            print(f"    Descripción : {skill.description}")
        print("-" * 60)

    return 0


def cmd_policy() -> int:
    """Muestra un resumen de las políticas de ejecución y seguridad."""
    summary = PolicyEngine.get_policy_summary()

    print("=" * 60)
    print(" POLÍTICAS DE EJECUCIÓN Y SEGURIDAD")
    print(" (Derivadas de AGENTS.md y policies/SECURITY.md)")
    print("=" * 60)

    sections = [
        ("1. COMANDOS PERMITIDOS SIN APROBACIÓN", "permitido_sin_aprobacion"),
        ("2. ACCIONES QUE REQUIEREN APROBACIÓN HUMANA", "requiere_aprobacion_humana"),
        ("3. SIEMPRE PROHIBIDO POR DEFECTO", "siempre_prohibido_por_defecto"),
        ("4. POLÍTICA HANA (DEV SOLO LECTURA)", "hana_read_only"),
        ("5. PROTECCIÓN DE PRODUCCIÓN", "proteccion_produccion"),
        ("6. POLÍTICA DE CONTROL DE VERSIONES (GIT)", "reglas_git"),
        ("7. GESTIÓN Y PROTECCIÓN DE SECRETOS", "manejo_secretos"),
    ]

    for title, key in sections:
        print(f"\n{title}:")
        items = summary.get(key, [])
        for item in items:
            print(f"  • {item}")

    print("\n" + "=" * 60)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construye el analizador de argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        prog="sap-b1-copilot",
        description="SAP B1 Engineering Copilot CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    subparsers.add_parser("status", help="Muestra el estado operativo del proyecto")
    subparsers.add_parser("skills", help="Lista las Skills descubiertas")
    subparsers.add_parser("policy", help="Muestra el resumen de políticas de seguridad y ejecución")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Punto de entrada principal para CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "status":
        return cmd_status()
    elif args.command == "skills":
        return cmd_skills()
    elif args.command == "policy":
        return cmd_policy()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
