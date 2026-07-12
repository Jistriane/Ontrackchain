#!/usr/bin/env python3
"""Tests for validate_serious_window_artifact.py"""

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

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
    "validate_serious_window_artifact",
    "scripts/validate_serious_window_artifact.py",
)


class ValidateSeriousWindowArtifactTests(unittest.TestCase):
    maxDiff = None

    def test_validate_p0_01_only(self) -> None:
        with TemporaryDirectory() as tmpdir:
            checks_dir = Path(tmpdir) / "checks"
            dossiers_dir = Path(tmpdir) / "dossiers"
            window_id = "stg-2026-07-06-a"

            checks_dir.mkdir(parents=True)
            dossiers_dir.mkdir(parents=True)
            (checks_dir / f"ownership-coverage-{window_id}.json").touch()
            (checks_dir / f"placeholders-{window_id}.json").touch()
            (checks_dir / f"handoff-{window_id}.json").touch()
            (checks_dir / f"oidc-preflight-{window_id}.json").touch()
            (checks_dir / f"external-preflight-{window_id}.json").touch()
            (dossiers_dir / f"{window_id}-dossier.json").touch()
            (checks_dir / f"{window_id}-oidc-readiness-bundle.json").touch()
            (dossiers_dir / f"{window_id}-oidc-readiness-bundle.md").touch()

            exit_code, payload = MODULE.validate_artifact(
                window_id=window_id,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                scope=["P0-01"],
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(payload["missing_artifacts"])
        self.assertGreater(len(payload["found_artifacts"]), 0)

    def test_validate_p0_01_missing_oidc_bundle(self) -> None:
        with TemporaryDirectory() as tmpdir:
            checks_dir = Path(tmpdir) / "checks"
            dossiers_dir = Path(tmpdir) / "dossiers"
            window_id = "stg-2026-07-06-a"

            checks_dir.mkdir(parents=True)
            dossiers_dir.mkdir(parents=True)
            (checks_dir / f"ownership-coverage-{window_id}.json").touch()
            (checks_dir / f"placeholders-{window_id}.json").touch()
            (checks_dir / f"handoff-{window_id}.json").touch()
            (checks_dir / f"oidc-preflight-{window_id}.json").touch()
            (checks_dir / f"external-preflight-{window_id}.json").touch()
            (dossiers_dir / f"{window_id}-dossier.json").touch()

            exit_code, payload = MODULE.validate_artifact(
                window_id=window_id,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                scope=["P0-01"],
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(len(payload["missing_artifacts"]), 2)

    def test_validate_p0_02_only(self) -> None:
        with TemporaryDirectory() as tmpdir:
            checks_dir = Path(tmpdir) / "checks"
            dossiers_dir = Path(tmpdir) / "dossiers"
            window_id = "stg-2026-07-06-a"

            checks_dir.mkdir(parents=True)
            dossiers_dir.mkdir(parents=True)
            (checks_dir / f"ownership-coverage-{window_id}.json").touch()
            (checks_dir / f"placeholders-{window_id}.json").touch()
            (checks_dir / f"handoff-{window_id}.json").touch()
            (checks_dir / f"oidc-preflight-{window_id}.json").touch()
            (checks_dir / f"external-preflight-{window_id}.json").touch()
            (checks_dir / f"{window_id}-regulatory-readiness-bundle.json").write_text(
                json.dumps(
                    {
                        "steps": {
                            "compliance_provider_runtime": {
                                "request_id": "req-comp-1",
                                "correlation": {"provider_converges_live": True},
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            (dossiers_dir / f"{window_id}-dossier.json").write_text(
                json.dumps(
                    {
                        "summaries": {
                            "regulatory_readiness_bundle": {
                                "scope": {
                                    "compliance_runtime_enabled": True,
                                    "eu_window_enabled": False,
                                },
                                "correlation": {
                                    "compliance_runtime_request_id": "req-comp-1",
                                    "compliance_runtime_provider_converges_live": True,
                                }
                                ,
                                "validation": {
                                    "compliance_runtime_scope_converges": True,
                                    "eu_window_scope_converges": True,
                                    "combined_regulatory_bundle_ready_for_validation": True,
                                },
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            exit_code, payload = MODULE.validate_artifact(
                window_id=window_id,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                scope=["P0-02"],
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(payload["missing_artifacts"])

    def test_validate_p0_03_only(self) -> None:
        with TemporaryDirectory() as tmpdir:
            checks_dir = Path(tmpdir) / "checks"
            dossiers_dir = Path(tmpdir) / "dossiers"
            window_id = "stg-2026-07-06-a"

            checks_dir.mkdir(parents=True)
            dossiers_dir.mkdir(parents=True)
            (checks_dir / f"ownership-coverage-{window_id}.json").touch()
            (checks_dir / f"placeholders-{window_id}.json").touch()
            (checks_dir / f"handoff-{window_id}.json").touch()
            (checks_dir / f"oidc-preflight-{window_id}.json").touch()
            (checks_dir / f"external-preflight-{window_id}.json").touch()
            (checks_dir / f"{window_id}-eu-sanctions-preflight.json").touch()
            (checks_dir / f"{window_id}-eu-sanctions-sync.json").touch()
            (checks_dir / f"{window_id}-regulatory-readiness-bundle.json").write_text(
                json.dumps(
                    {
                        "steps": {
                            "eu_sanctions_window": {
                                "request_id": "req-eu-1",
                                "correlation": {"eu_window_converges_ready": True},
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            (dossiers_dir / f"{window_id}-dossier.json").write_text(
                json.dumps(
                    {
                        "summaries": {
                            "regulatory_readiness_bundle": {
                                "scope": {
                                    "compliance_runtime_enabled": False,
                                    "eu_window_enabled": True,
                                },
                                "correlation": {
                                    "eu_window_request_id": "req-eu-1",
                                    "eu_window_converges_ready": True,
                                }
                                ,
                                "validation": {
                                    "compliance_runtime_scope_converges": True,
                                    "eu_window_scope_converges": True,
                                    "combined_regulatory_bundle_ready_for_validation": True,
                                },
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            exit_code, payload = MODULE.validate_artifact(
                window_id=window_id,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                scope=["P0-03"],
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(payload["missing_artifacts"])

    def test_validate_p0_02_p0_03_consolidated(self) -> None:
        with TemporaryDirectory() as tmpdir:
            checks_dir = Path(tmpdir) / "checks"
            dossiers_dir = Path(tmpdir) / "dossiers"
            window_id = "stg-2026-07-06-a"

            checks_dir.mkdir(parents=True)
            dossiers_dir.mkdir(parents=True)
            (checks_dir / f"ownership-coverage-{window_id}.json").touch()
            (checks_dir / f"placeholders-{window_id}.json").touch()
            (checks_dir / f"handoff-{window_id}.json").touch()
            (checks_dir / f"oidc-preflight-{window_id}.json").touch()
            (checks_dir / f"external-preflight-{window_id}.json").touch()
            (dossiers_dir / f"{window_id}-dossier.json").touch()
            (checks_dir / f"{window_id}-regulatory-readiness-bundle.json").write_text(
                json.dumps(
                    {
                        "readiness": {
                            "regulatory_bundle": {"readiness_status": "ready_for_validation"},
                        },
                        "steps": {
                            "compliance_provider_runtime": {
                                "request_id": "req-comp-1",
                                "correlation": {"provider_converges_live": True},
                            },
                            "eu_sanctions_window": {
                                "request_id": "req-eu-1",
                                "correlation": {"source_url_matches_expected": True, "eu_window_converges_ready": True},
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            (dossiers_dir / f"{window_id}-regulatory-readiness-bundle.md").touch()
            (dossiers_dir / f"{window_id}-dossier.json").write_text(
                json.dumps(
                    {
                        "summaries": {
                            "regulatory_readiness_bundle": {
                                "scope": {
                                    "compliance_runtime_enabled": True,
                                    "eu_window_enabled": True,
                                },
                                "correlation": {
                                    "compliance_runtime_request_id": "req-comp-1",
                                    "compliance_runtime_provider_converges_live": True,
                                    "eu_window_request_id": "req-eu-1",
                                    "eu_source_url_matches_expected": True,
                                    "eu_window_converges_ready": True,
                                },
                                "validation": {
                                    "compliance_runtime_scope_converges": True,
                                    "eu_window_scope_converges": True,
                                    "combined_regulatory_bundle_ready_for_validation": True,
                                }
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            exit_code, payload = MODULE.validate_artifact(
                window_id=window_id,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                scope=["P0-02", "P0-03"],
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(payload["missing_artifacts"])

    def test_validate_all_p0_items(self) -> None:
        with TemporaryDirectory() as tmpdir:
            checks_dir = Path(tmpdir) / "checks"
            dossiers_dir = Path(tmpdir) / "dossiers"
            window_id = "stg-2026-07-06-a"

            checks_dir.mkdir(parents=True)
            dossiers_dir.mkdir(parents=True)
            (checks_dir / f"ownership-coverage-{window_id}.json").touch()
            (checks_dir / f"placeholders-{window_id}.json").touch()
            (checks_dir / f"handoff-{window_id}.json").touch()
            (checks_dir / f"oidc-preflight-{window_id}.json").touch()
            (checks_dir / f"external-preflight-{window_id}.json").touch()
            (dossiers_dir / f"{window_id}-dossier.json").touch()
            (checks_dir / f"{window_id}-oidc-readiness-bundle.json").touch()
            (dossiers_dir / f"{window_id}-oidc-readiness-bundle.md").touch()
            (checks_dir / f"{window_id}-regulatory-readiness-bundle.json").write_text(
                json.dumps(
                    {
                        "readiness": {
                            "regulatory_bundle": {"readiness_status": "ready_for_validation"},
                        },
                        "steps": {
                            "compliance_provider_runtime": {
                                "request_id": "req-comp-1",
                                "correlation": {"provider_converges_live": True},
                            },
                            "eu_sanctions_window": {
                                "request_id": "req-eu-1",
                                "correlation": {"source_url_matches_expected": True, "eu_window_converges_ready": True},
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            (dossiers_dir / f"{window_id}-regulatory-readiness-bundle.md").touch()
            (dossiers_dir / f"{window_id}-dossier.json").write_text(
                json.dumps(
                    {
                        "summaries": {
                            "regulatory_readiness_bundle": {
                                "scope": {
                                    "compliance_runtime_enabled": True,
                                    "eu_window_enabled": True,
                                },
                                "correlation": {
                                    "compliance_runtime_request_id": "req-comp-1",
                                    "compliance_runtime_provider_converges_live": True,
                                    "eu_window_request_id": "req-eu-1",
                                    "eu_source_url_matches_expected": True,
                                    "eu_window_converges_ready": True,
                                },
                                "validation": {
                                    "compliance_runtime_scope_converges": True,
                                    "eu_window_scope_converges": True,
                                    "combined_regulatory_bundle_ready_for_validation": True,
                                }
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            exit_code, payload = MODULE.validate_artifact(
                window_id=window_id,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                scope=["P0-01", "P0-02", "P0-03"],
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertFalse(payload["missing_artifacts"])
        self.assertGreater(len(payload["found_artifacts"]), 0)

    def test_validate_combined_window_fails_without_correlation_guards(self) -> None:
        with TemporaryDirectory() as tmpdir:
            checks_dir = Path(tmpdir) / "checks"
            dossiers_dir = Path(tmpdir) / "dossiers"
            window_id = "stg-2026-07-06-a"

            checks_dir.mkdir(parents=True)
            dossiers_dir.mkdir(parents=True)
            (checks_dir / f"ownership-coverage-{window_id}.json").touch()
            (checks_dir / f"placeholders-{window_id}.json").touch()
            (checks_dir / f"handoff-{window_id}.json").touch()
            (checks_dir / f"oidc-preflight-{window_id}.json").touch()
            (checks_dir / f"external-preflight-{window_id}.json").touch()
            (dossiers_dir / f"{window_id}-dossier.json").write_text(
                json.dumps(
                    {
                        "summaries": {
                            "regulatory_readiness_bundle": {
                                "scope": {
                                    "compliance_runtime_enabled": True,
                                    "eu_window_enabled": True,
                                },
                                "correlation": {
                                    "compliance_runtime_request_id": "",
                                    "compliance_runtime_provider_converges_live": False,
                                    "eu_window_request_id": "",
                                    "eu_source_url_matches_expected": False,
                                    "eu_window_converges_ready": False,
                                },
                                "validation": {
                                    "compliance_runtime_scope_converges": False,
                                    "eu_window_scope_converges": False,
                                    "combined_regulatory_bundle_ready_for_validation": False,
                                }
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            (checks_dir / f"{window_id}-oidc-readiness-bundle.json").touch()
            (dossiers_dir / f"{window_id}-oidc-readiness-bundle.md").touch()
            (checks_dir / f"{window_id}-regulatory-readiness-bundle.json").write_text(
                json.dumps(
                    {
                        "readiness": {
                            "regulatory_bundle": {"readiness_status": "ready"},
                        },
                        "steps": {
                            "compliance_provider_runtime": {
                                "request_id": "",
                                "correlation": {"provider_converges_live": False},
                            },
                            "eu_sanctions_window": {
                                "request_id": "",
                                "correlation": {"source_url_matches_expected": False, "eu_window_converges_ready": False},
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            (dossiers_dir / f"{window_id}-regulatory-readiness-bundle.md").touch()

            exit_code, payload = MODULE.validate_artifact(
                window_id=window_id,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                scope=["P0-01", "P0-02", "P0-03"],
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertTrue(any("request_id ausente" in error for error in payload["errors"]))
        self.assertTrue(any("ready_for_validation" in error for error in payload["errors"]))

    def test_validate_fails_when_dossier_scope_diverges_from_requested_scope(self) -> None:
        with TemporaryDirectory() as tmpdir:
            checks_dir = Path(tmpdir) / "checks"
            dossiers_dir = Path(tmpdir) / "dossiers"
            window_id = "stg-2026-07-06-a"

            checks_dir.mkdir(parents=True)
            dossiers_dir.mkdir(parents=True)
            (checks_dir / f"ownership-coverage-{window_id}.json").touch()
            (checks_dir / f"placeholders-{window_id}.json").touch()
            (checks_dir / f"handoff-{window_id}.json").touch()
            (checks_dir / f"oidc-preflight-{window_id}.json").touch()
            (checks_dir / f"external-preflight-{window_id}.json").touch()
            (checks_dir / f"{window_id}-regulatory-readiness-bundle.json").write_text(
                json.dumps(
                    {
                        "steps": {
                            "compliance_provider_runtime": {
                                "request_id": "req-comp-1",
                                "correlation": {"provider_converges_live": True},
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            (dossiers_dir / f"{window_id}-dossier.json").write_text(
                json.dumps(
                    {
                        "summaries": {
                            "regulatory_readiness_bundle": {
                                "scope": {
                                    "compliance_runtime_enabled": False,
                                    "eu_window_enabled": True,
                                },
                                "correlation": {
                                    "compliance_runtime_request_id": "req-comp-1",
                                    "compliance_runtime_provider_converges_live": True,
                                },
                                "validation": {
                                    "compliance_runtime_scope_converges": True,
                                    "eu_window_scope_converges": True,
                                    "combined_regulatory_bundle_ready_for_validation": True,
                                },
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            exit_code, payload = MODULE.validate_artifact(
                window_id=window_id,
                checks_dir=checks_dir,
                dossiers_dir=dossiers_dir,
                scope=["P0-02"],
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "failed")
        self.assertTrue(any("diverge do escopo validado" in error for error in payload["errors"]))


if __name__ == "__main__":
    unittest.main()
