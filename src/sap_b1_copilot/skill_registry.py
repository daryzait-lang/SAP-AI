"""Registro y descubrimiento de Skills para SAP B1 Engineering Copilot.

Descubre automáticamente las Skills dentro del directorio /skills.
Una Skill es válida únicamente si es un directorio y contiene un archivo SKILL.md.
Devuelve como mínimo: name, path, skill_file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config import load_config


@dataclass(frozen=True)
class SkillMetadata:
    """Metadatos de una Skill descubierta."""

    name: str
    path: Path
    skill_file: Path
    description: str = ""

    def to_dict(self) -> dict[str, str]:
        """Representación serializable de la Skill."""
        return {
            "name": self.name,
            "path": str(self.path),
            "skill_file": str(self.skill_file),
            "description": self.description,
        }

    def read_content(self) -> str:
        """Lee el contenido completo del archivo SKILL.md."""
        return self.skill_file.read_text(encoding="utf-8")


def _parse_frontmatter(content: str) -> dict[str, str]:
    """Extrae metadatos de frontmatter YAML simple (---\n...\n---) si existe."""
    metadata: dict[str, str] = {}
    if not content.startswith("---"):
        return metadata

    parts = content.split("---", 2)
    if len(parts) < 3:
        return metadata

    frontmatter_block = parts[1]
    for line in frontmatter_block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, val = line.split(":", 1)
        val_clean = val.strip().strip('"').strip("'")
        metadata[key.strip()] = val_clean

    return metadata


class SkillRegistry:
    """Registro que gestiona el descubrimiento e inspección de Skills."""

    def __init__(self, skills_dir: Optional[Path] = None) -> None:
        if skills_dir is None:
            config = load_config()
            self.skills_dir = config.get_skills_dir()
        else:
            self.skills_dir = Path(skills_dir).resolve()

        self._skills: dict[str, SkillMetadata] = {}
        self.discover()

    def discover(self) -> list[SkillMetadata]:
        """Descubre automáticamente todas las Skills válidas dentro de skills_dir.

        Una Skill se considera válida solo si contiene SKILL.md.
        """
        self._skills.clear()

        if not self.skills_dir.is_dir():
            return []

        for item in sorted(self.skills_dir.iterdir()):
            if not item.is_dir():
                continue

            skill_file = item / "SKILL.md"
            if not skill_file.is_file():
                continue

            name = item.name
            description = ""

            try:
                content = skill_file.read_text(encoding="utf-8")
                fm = _parse_frontmatter(content)
                if "name" in fm and fm["name"]:
                    name = fm["name"]
                if "description" in fm and fm["description"]:
                    description = fm["description"]
                elif not description:
                    # Extraer primera línea que no sea encabezado si no hay frontmatter
                    for line in content.splitlines():
                        stripped = line.strip()
                        if stripped and not stripped.startswith(("#", "---")):
                            description = stripped
                            break
            except Exception:
                # Si falla la lectura de descripción, conservar nombre del directorio
                pass

            metadata = SkillMetadata(
                name=name,
                path=item,
                skill_file=skill_file,
                description=description,
            )
            self._skills[name] = metadata

        return list(self._skills.values())

    def list_skills(self) -> list[SkillMetadata]:
        """Devuelve la lista ordenada de Skills descubiertas."""
        return list(self._skills.values())

    def get_skill(self, name: str) -> Optional[SkillMetadata]:
        """Obtiene una Skill específica por nombre."""
        return self._skills.get(name)

    def count(self) -> int:
        """Devuelve la cantidad de Skills registradas."""
        return len(self._skills)
