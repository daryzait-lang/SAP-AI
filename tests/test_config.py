"""Pruebas unitarias para config.py de SAP B1 Engineering Copilot."""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import sys
# Asegurar que src esté en el path de importación
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from sap_b1_copilot.config import AppConfig, load_config, _parse_simple_yaml


class TestConfig(unittest.TestCase):
    """Conjunto de pruebas para la gestión de configuración y seguridad."""

    def test_default_config_loading(self):
        """Verifica que la configuración por defecto sea DEV y segura."""
        config = load_config(environ={})
        self.assertEqual(config.environment, "DEV")
        self.assertFalse(config.is_production())
        self.assertFalse(config.is_production_allowed())
        self.assertTrue(config.hana_read_only)
        self.assertIn("SAP B1", config.project_name)

    def test_production_blocked_by_default(self):
        """Verifica que la producción esté terminantemente bloqueada por defecto."""
        # Incluso si se pasa un ambiente PROD sin bandera afirmativa de habilitación
        config = load_config(environ={"SAP_COPILOT_ENV": "PROD"})
        self.assertEqual(config.environment, "PROD")
        self.assertTrue(config.is_production())
        self.assertFalse(config.is_production_allowed())

    def test_production_explicit_enablement(self):
        """Verifica que producción solo se active con autorización explícita."""
        config = load_config(environ={"SAP_COPILOT_ENV": "PROD", "SAP_ALLOW_PRODUCTION": "true"})
        self.assertTrue(config.is_production())
        self.assertTrue(config.is_production_allowed())

        # Si se indica explícitamente false
        config_disabled = load_config(environ={"SAP_ALLOW_PRODUCTION": "false"})
        self.assertFalse(config_disabled.is_production_allowed())

    def test_project_paths_resolution(self):
        """Verifica que las rutas del proyecto se resuelvan correctamente."""
        config = load_config()
        self.assertTrue(config.project_root.exists())
        self.assertTrue(config.get_skills_dir().exists())
        self.assertTrue(config.get_policies_dir().exists())
        self.assertTrue(config.get_config_dir().exists())
        self.assertTrue(config.get_src_dir().exists())

    def test_safe_summary_has_no_secrets(self):
        """Verifica que safe_summary() y __repr__() no contengan secretos ni campos sensibles."""
        config = load_config()
        summary = config.safe_summary()

        forbidden_keys = {"password", "secret", "b1session", "token", "key", "credential"}
        for k in summary.keys():
            self.assertNotIn(k.lower(), forbidden_keys)

        repr_str = repr(config).lower()
        for forbidden in ("password", "b1session", "token", "secret"):
            self.assertNotIn(forbidden, repr_str)

    def test_parse_simple_yaml(self):
        """Verifica que el parser YAML sin dependencias funcione con tipos básicos."""
        yaml_text = """
        # Comentario de prueba
        project:
          name: "Test Project"
        environment: DEV
        allow_production: false
        timeout: 45
        """
        parsed = _parse_simple_yaml(yaml_text)
        self.assertEqual(parsed.get("environment"), "DEV")
        self.assertIs(parsed.get("allow_production"), False)
        self.assertEqual(parsed.get("timeout"), 45)
        self.assertIn("project", parsed)
        self.assertEqual(parsed["project"].get("name"), "Test Project")


if __name__ == "__main__":
    unittest.main()
