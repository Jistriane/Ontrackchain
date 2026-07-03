import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT_DIR / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao foi possivel carregar modulo em {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load_module(
    "build_staging_release_dossier",
    "scripts/build_staging_release_dossier.py",
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class BuildStagingReleaseDossierTests(unittest.TestCase):
    maxDiff = None

    def test_build_payload_aggregates_ok_status_and_attachment_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            window_packet = base / "window-packet.md"
            ownership_check = base / "ownership.json"
            placeholder_check = base / "placeholders.json"
            handoff_check = base / "handoff.json"
            homologation_artifact = base / "homologation.json"
            homologation_manifest = base / "homologation.manifest.json"
            oidc_bundle = base / "oidc-bundle.json"
            oidc_bundle_summary = base / "oidc-bundle.md"
            regulatory_bundle = base / "regulatory-bundle.json"
            regulatory_bundle_summary = base / "regulatory-bundle.md"

            window_packet.write_text("# Packet\n", encoding="utf-8")
            _write_json(
                ownership_check,
                {
                    "status": "ok",
                    "missing_in_matrix": [],
                    "stale_in_matrix": [],
                    "incomplete_mappings": [],
                },
            )
            _write_json(
                placeholder_check,
                {
                    "status": "ok",
                    "unresolved_placeholders": [],
                    "missing_required": [],
                    "empty_required": [],
                },
            )
            _write_json(
                handoff_check,
                {
                    "status": "ok",
                    "missing_groups": [],
                    "incomplete_groups": [],
                    "invalid_statuses": [],
                    "invalid_dates": [],
                },
            )
            _write_json(
                homologation_artifact,
                {
                    "status": "ok",
                    "mode": "both",
                    "artifact_file": "/tmp/external_homologation_both.json",
                    "manifest_file": "/tmp/external_homologation_both.json.manifest.json",
                    "runs": {
                        "compliance": {"request_id": "req_comp_1"},
                        "rpc": {"request_id": "req_rpc_1", "case_id": "case_1"},
                    },
                },
            )
            _write_json(
                homologation_manifest,
                {
                    "kind": "external_homologation_evidence",
                    "status": "ok",
                    "artifact_file_sha256": "abc123",
                },
            )
            _write_json(
                oidc_bundle,
                {
                    "kind": "oidc_readiness_bundle",
                    "status": "ok",
                    "scope": {
                        "mfa_external_provider_homologated": "true",
                        "expected_oidc_provider": "keycloak",
                    },
                    "steps": {
                        "oidc_preflight": {"status": "ok"},
                        "smoke_auth_oidc_mode": {"status": "ok"},
                    },
                },
            )
            oidc_bundle_summary.write_text("# OIDC Bundle\n", encoding="utf-8")
            _write_json(
                regulatory_bundle,
                {
                    "kind": "regulatory_readiness_bundle",
                    "status": "ok",
                    "scope": {
                        "compliance_runtime_enabled": True,
                        "eu_window_enabled": True,
                    },
                    "steps": {
                        "compliance_provider_runtime": {"status": "ok"},
                        "eu_sanctions_window": {"status": "ok"},
                    },
                },
            )
            regulatory_bundle_summary.write_text("# Regulatory Bundle\n", encoding="utf-8")

            payload = MODULE.build_dossier_payload(
                window_id="stg-2026-06-29-a",
                window_packet=window_packet,
                ownership_coverage_check=ownership_check,
                placeholder_check=placeholder_check,
                handoff_check=handoff_check,
                homologation_artifact=homologation_artifact,
                homologation_manifest=homologation_manifest,
                oidc_readiness_bundle=oidc_bundle,
                oidc_readiness_bundle_summary=oidc_bundle_summary,
                regulatory_readiness_bundle=regulatory_bundle,
                regulatory_readiness_bundle_summary=regulatory_bundle_summary,
                generated_at="2026-06-29T12:00:00+00:00",
            )

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["checks_status"]["homologation"], "ok")
        self.assertEqual(payload["checks_status"]["oidc_readiness_bundle"], "ok")
        self.assertEqual(payload["checks_status"]["regulatory_readiness_bundle"], "ok")
        self.assertEqual(
            payload["summaries"]["oidc_readiness_bundle"]["steps"]["smoke_auth_oidc_mode"],
            "ok",
        )
        self.assertEqual(payload["summaries"]["homologation"]["runs"]["rpc_case_id"], "case_1")
        self.assertEqual(
            payload["summaries"]["regulatory_readiness_bundle"]["steps"]["eu_sanctions_window"],
            "ok",
        )
        self.assertIn("oidc_readiness_bundle_summary", payload["artifacts"])
        self.assertIn("regulatory_readiness_bundle_summary", payload["artifacts"])
        self.assertIn("sha256", payload["artifacts"]["window_packet"])

    def test_build_payload_fails_when_required_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            existing = base / "window-packet.md"
            existing.write_text("# Packet\n", encoding="utf-8")

            payload = MODULE.build_dossier_payload(
                window_id="stg-2026-06-29-a",
                window_packet=existing,
                ownership_coverage_check=base / "missing-ownership.json",
                placeholder_check=base / "missing-placeholders.json",
                handoff_check=base / "missing-handoff.json",
                homologation_artifact=base / "missing-homologation.json",
                homologation_manifest=base / "missing-homologation.manifest.json",
                oidc_readiness_bundle=base / "missing-oidc-bundle.json",
                oidc_readiness_bundle_summary=base / "missing-oidc-bundle.md",
                regulatory_readiness_bundle=base / "missing-regulatory-bundle.json",
                regulatory_readiness_bundle_summary=base / "missing-regulatory-bundle.md",
                generated_at="2026-06-29T12:00:00+00:00",
            )

        self.assertEqual(payload["status"], "failed")
        self.assertTrue(any(error.startswith("arquivo_ausente:") for error in payload["errors"]))

    def test_main_writes_dossier_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            window_packet = base / "window-packet.md"
            ownership_check = base / "ownership.json"
            placeholder_check = base / "placeholders.json"
            handoff_check = base / "handoff.json"
            homologation_artifact = base / "homologation.json"
            homologation_manifest = base / "homologation.manifest.json"
            oidc_bundle = base / "oidc-bundle.json"
            oidc_bundle_summary = base / "oidc-bundle.md"
            regulatory_bundle = base / "regulatory-bundle.json"
            regulatory_bundle_summary = base / "regulatory-bundle.md"
            output_dir = base / "dossiers"

            window_packet.write_text("# Packet\n", encoding="utf-8")
            _write_json(ownership_check, {"status": "ok", "missing_in_matrix": [], "stale_in_matrix": [], "incomplete_mappings": []})
            _write_json(placeholder_check, {"status": "ok", "unresolved_placeholders": [], "missing_required": [], "empty_required": []})
            _write_json(handoff_check, {"status": "ok", "missing_groups": [], "incomplete_groups": [], "invalid_statuses": [], "invalid_dates": []})
            _write_json(homologation_artifact, {"status": "ok", "mode": "both", "artifact_file": "/tmp/h.json", "manifest_file": "/tmp/h.json.manifest.json", "runs": {}})
            _write_json(homologation_manifest, {"kind": "external_homologation_evidence", "status": "ok"})
            _write_json(oidc_bundle, {"kind": "oidc_readiness_bundle", "status": "ok", "scope": {}, "steps": {}})
            oidc_bundle_summary.write_text("# OIDC Bundle\n", encoding="utf-8")
            _write_json(regulatory_bundle, {"kind": "regulatory_readiness_bundle", "status": "ok", "scope": {}, "steps": {}})
            regulatory_bundle_summary.write_text("# Regulatory Bundle\n", encoding="utf-8")

            stdout = io.StringIO()
            with patch.object(
                sys,
                "argv",
                [
                    "build_staging_release_dossier.py",
                    "--window-id",
                    "stg-2026-06-29-a",
                    "--window-packet",
                    str(window_packet),
                    "--ownership-coverage-check",
                    str(ownership_check),
                    "--placeholder-check",
                    str(placeholder_check),
                    "--handoff-check",
                    str(handoff_check),
                    "--homologation-artifact",
                    str(homologation_artifact),
                    "--homologation-manifest",
                    str(homologation_manifest),
                    "--oidc-readiness-bundle",
                    str(oidc_bundle),
                    "--oidc-readiness-bundle-summary",
                    str(oidc_bundle_summary),
                    "--regulatory-readiness-bundle",
                    str(regulatory_bundle),
                    "--regulatory-readiness-bundle-summary",
                    str(regulatory_bundle_summary),
                    "--output-dir",
                    str(output_dir),
                    "--generated-at",
                    "2026-06-29T12:00:00+00:00",
                ],
            ):
                with redirect_stdout(stdout):
                    exit_code = MODULE.main()

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["status"], "ok")
            artifact_file = Path(payload["artifact_file"])
            manifest_file = Path(payload["manifest_file"])
            self.assertTrue(artifact_file.exists())
            self.assertTrue(manifest_file.exists())
            manifest_payload = json.loads(manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest_payload["status"], "ok")
            self.assertEqual(manifest_payload["window_id"], "stg-2026-06-29-a")


if __name__ == "__main__":
    unittest.main()
