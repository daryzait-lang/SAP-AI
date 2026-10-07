"""Pruebas unitarias para skill_registry.py de SAP B1 Engineering Copilot."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import sys
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from sap_b1_copilot.skill_registry import SkillRegistry, SkillMetadata


class TestSkillRegistry(unittest.TestCase):
    """Conjunto de pruebas para el descubrimiento y validación de Skills."""

    def setUp(self):
        self.registry = SkillRegistry()

    def test_discover_six_existing_skills(self):
        """Verifica que se descubran exactamente las 6 Skills requeridas por el proyecto."""
        skills = self.registry.list_skills()
        self.assertEqual(len(skills), 6)

        expected_skills = {
            "crystal-runtime-guardian",
            "hana-report-optimizer",
            "sap-legacy-modernizer",
            "sap-test-engineer",
            "sl-model-generator",
            "ui5-premium-crafter",
        }
        discovered_names = {s.name for s in skills}
        self.assertEqual(discovered_names, expected_skills)

    def test_skill_attributes_present(self):
        """Verifica que cada Skill descubierta incluya name, path y skill_file."""
        for skill in self.registry.list_skills():
            self.assertTrue(bool(skill.name))
            self.assertIsInstance(skill.path, Path)
            self.assertTrue(skill.path.is_dir())
            self.assertIsInstance(skill.skill_file, Path)
            self.assertTrue(skill.skill_file.is_file())
            self.assertEqual(skill.skill_file.name, "SKILL.md")

            skill_dict = skill.to_dict()
            self.assertIn("name", skill_dict)
            self.assertIn("path", skill_dict)
            self.assertIn("skill_file", skill_dict)
            self.assertIn("description", skill_dict)

    def test_get_individual_skill(self):
        """Verifica que se pueda consultar una Skill por su nombre."""
        skill = self.registry.get_skill("sap-legacy-modernizer")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "sap-legacy-modernizer")
        self.assertIn("VB.NET", skill.read_content())

    def test_ignore_directories_without_skill_md(self):
        """Verifica que directorios sin SKILL.md no sean registrados como Skills válidas."""
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Carpeta válida (con SKILL.md)
            valid_skill = tmp_path / "custom-valid-skill"
            valid_skill.mkdir()
            (valid_skill / "SKILL.md").write_text(
                "---\nname: custom-valid-skill\ndescription: Skill de prueba\n---\n# Docs",
                encoding="utf-8",
            )

            # Carpeta inválida (sin SKILL.md)
            invalid_dir = tmp_path / "not-a-skill"
            invalid_dir.mkdir()
            (invalid_dir / "README.md").write_text("No es una skill", encoding="utf-8")

            # Archivo suelto
            (tmp_path / "stray_file.txt").write_text("Archivo suelto", encoding="utf-8")

            test_registry = SkillRegistry(tmp_path)
            discovered = test_registry.list_skills()

            self.assertEqual(len(discovered), 1)
            self.assertEqual(discovered[0].name, "custom-valid-skill")


if __name__ == "__main__":
    unittest.main()
