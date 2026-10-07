"""Pruebas unitarias para policies.py de SAP B1 Engineering Copilot."""

import unittest
from pathlib import Path

import sys
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from sap_b1_copilot.policies import PolicyDecision, PolicyEngine


class TestPolicies(unittest.TestCase):
    """Conjunto de pruebas para la validación de políticas y seguridad."""

    # 1. Pruebas de HANA READ-ONLY
    def test_hana_select_allowed(self):
        """Verifica que consultas SELECT en HANA DEV estén permitidas."""
        res1 = PolicyEngine.evaluate_sql("SELECT CardCode, CardName FROM OCRD WHERE FrozenFor = 'N'")
        self.assertEqual(res1.decision, PolicyDecision.ALLOWED)
        self.assertTrue(res1.is_allowed)

        res2 = PolicyEngine.evaluate_sql("EXPLAIN PLAN FOR SELECT * FROM OINV")
        self.assertEqual(res2.decision, PolicyDecision.ALLOWED)

    def test_hana_mutations_forbidden(self):
        """Verifica que cualquier mutación DML o DDL en HANA esté estrictamente prohibida."""
        mutating_statements = [
            "INSERT INTO OCRD (CardCode, CardName) VALUES ('C001', 'Test')",
            "UPDATE OCRD SET CardName = 'Modified' WHERE CardCode = 'C001'",
            "DELETE FROM OCRD WHERE CardCode = 'C001'",
            "UPSERT OINV (DocEntry) VALUES (1)",
            "MERGE INTO OINV USING DUAL ON (1=1) WHEN MATCHED THEN UPDATE SET DocTotal = 100",
            "DROP TABLE OINV",
            "ALTER TABLE OCRD ADD (U_CustomField NVARCHAR(50))",
            "TRUNCATE TABLE ADOC",
            "CREATE TABLE CustomTable (ID INT)",
        ]
        for stmt in mutating_statements:
            res = PolicyEngine.evaluate_sql(stmt)
            self.assertEqual(
                res.decision,
                PolicyDecision.FORBIDDEN,
                f"La sentencia no fue bloqueada: {stmt}",
            )
            self.assertTrue(res.is_forbidden)

    # 2. Pruebas de Protección de Producción
    def test_production_protection_blocked_by_default(self):
        """Verifica que el acceso a entornos productivos esté bloqueado por defecto."""
        res_prod = PolicyEngine.evaluate_production_access("PROD")
        self.assertEqual(res_prod.decision, PolicyDecision.FORBIDDEN)
        self.assertTrue(res_prod.is_forbidden)

        res_production = PolicyEngine.evaluate_production_access("production")
        self.assertEqual(res_production.decision, PolicyDecision.FORBIDDEN)

    def test_production_access_with_explicit_approval(self):
        """Verifica que con aprobación explícita pase a REQUIRES_APPROVAL para supervisión."""
        res = PolicyEngine.evaluate_production_access("PROD", approved=True)
        self.assertEqual(res.decision, PolicyDecision.REQUIRES_APPROVAL)

    def test_dev_access_allowed(self):
        """Verifica que el acceso a DEV esté permitido por defecto."""
        res = PolicyEngine.evaluate_production_access("DEV")
        self.assertEqual(res.decision, PolicyDecision.ALLOWED)

    # 3. Pruebas de Reglas Git
    def test_git_push_direct_to_main_forbidden(self):
        """Verifica que push directo a main esté estrictamente prohibido."""
        res = PolicyEngine.evaluate_git_push("main")
        self.assertEqual(res.decision, PolicyDecision.FORBIDDEN)
        self.assertTrue(res.is_forbidden)

        # También mediante comando directo
        cmd_res = PolicyEngine.evaluate_command("git push origin main")
        self.assertEqual(cmd_res.decision, PolicyDecision.FORBIDDEN)

    def test_git_push_task_branch_allowed(self):
        """Verifica que push a rama de tarea esté permitido."""
        res = PolicyEngine.evaluate_git_push("agent/bootstrap-copilot")
        self.assertEqual(res.decision, PolicyDecision.ALLOWED)

    def test_git_force_push_requires_approval(self):
        """Verifica que force push requiera aprobación humana obligatoria."""
        res = PolicyEngine.evaluate_git_push("agent/bootstrap-copilot", force=True)
        self.assertEqual(res.decision, PolicyDecision.REQUIRES_APPROVAL)

        cmd_res = PolicyEngine.evaluate_command("git push origin agent/task --force")
        self.assertEqual(cmd_res.decision, PolicyDecision.REQUIRES_APPROVAL)

    def test_git_auto_merge_forbidden(self):
        """Verifica que merge automático esté estrictamente prohibido."""
        res = PolicyEngine.evaluate_git_merge("main", automated=True)
        self.assertEqual(res.decision, PolicyDecision.FORBIDDEN)

    # 4. Pruebas de Comandos Permitidos sin Aprobación
    def test_safe_commands_allowed(self):
        """Verifica comandos de solo inspección y pruebas permitidos sin aprobación."""
        safe_commands = [
            "git status",
            "git diff",
            "git log -n 5",
            "git branch",
            "git checkout agent/task",
            "dotnet restore",
            "dotnet build",
            "dotnet test",
            "python -m sap_b1_copilot.cli status",
            "npm test",
        ]
        for cmd in safe_commands:
            res = PolicyEngine.evaluate_command(cmd)
            self.assertEqual(res.decision, PolicyDecision.ALLOWED, f"Comando bloqueado indebidamente: {cmd}")

    # 5. Pruebas de Acciones que Requieren Aprobación Humana
    def test_actions_requiring_human_approval(self):
        """Verifica que instalaciones y cambios del sistema requieran aprobación."""
        approval_commands = [
            "pip install requests",
            "npm install axios",
            "choco install git",
            "winget install Microsoft.DotNet.SDK.9",
            "reg add HKLM\\Software\\Test",
            "net start SAPService",
            "rm -rf ./node_modules",
        ]
        for cmd in approval_commands:
            res = PolicyEngine.evaluate_command(cmd)
            self.assertEqual(
                res.decision,
                PolicyDecision.REQUIRES_APPROVAL,
                f"Comando crítico no requirió aprobación: {cmd}",
            )

    # 6. Pruebas de Detección y Sanitización de Secretos
    def test_secret_sanitization(self):
        """Verifica que contraseñas, tokens y B1SESSION se enmascaren adecuadamente."""
        sample_log = "Error connecting: password=Secret1234! and B1SESSION=9B2A4C6D8E1F"
        sanitized = PolicyEngine.sanitize_text(sample_log)
        self.assertNotIn("Secret1234!", sanitized)
        self.assertNotIn("9B2A4C6D8E1F", sanitized)
        self.assertIn("***REDACTED***", sanitized)

    def test_secret_detection(self):
        """Verifica la detección de patrones de credenciales."""
        text_with_secrets = "Authorization: Bearer abcdef1234567890abcdef and api_key='sk-123456789012345678901234'"
        findings = PolicyEngine.detect_potential_secrets(text_with_secrets)
        self.assertTrue(len(findings) >= 1)


if __name__ == "__main__":
    unittest.main()
