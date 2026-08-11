# SPDX-FileCopyrightText: 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests de salida SARIF 2.1.0 (feature 002).

Guarda de integridad LOCAL del schema (no sincronización con upstream):
el schema es un SNAPSHOT de la rama `main` de oasis-tcs/sarif-spec tomado el
2026-07-13. Si el archivo local cambia sin querer, el test falla ruidosamente.
NO está pensado para detectar cambios en OASIS (es un snapshot, no un release).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import jsonschema
except ImportError:  # pragma: no cover
    pytest.skip("jsonschema no instalado (extra [testing])", allow_module_level=True)

from qchem_leak_screen.core.dataclasses import MolInput, PropPrediction, Verdict
from qchem_leak_screen.core.report import to_sarif, InputRef
from qchem_leak_screen.core.rules import apply_rules

THIS_DIR = Path(__file__).parent
FIXTURES = THIS_DIR / "fixtures"
SCHEMA_PATH = FIXTURES / "sarif_schema_2.1.0.json"
SCHEMA_SHA_PATH = FIXTURES / "sarif_schema_2.1.0.json.sha256"
# Hash local fijado el 2026-07-13 (snapshot de oasis-tcs/sarif-spec main).
EXPECTED_SHA256 = "c3b4bb2d6093897483348925aaa73af03b3e3f4bd4ca38cef26dcb4212a2682e"

# Fixtures de moléculas viven en el paquete (no en tests/): los reusa el MVP.
PKG_FIXTURES = Path(__file__).parent.parent / "qchem_leak_screen" / "fixtures"


# ---------------------------------------------------------------------------
# Guarda de integridad LOCAL del schema (S010 / decisión de Sil 2026-07-13)
# ---------------------------------------------------------------------------
def test_schema_integrity_local():
    """Falla si el schema local cambió sin querer (no si OASIS cambia el suyo)."""
    assert SCHEMA_PATH.exists(), "falta el schema SARIF local"
    import hashlib

    data = SCHEMA_PATH.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    assert actual == EXPECTED_SHA256, (
        f"Schema SARIF local modificado: {actual} != {EXPECTED_SHA256} "
        f"(snapshot oasis-tcs/sarif-spec main @ 2026-07-13)"
    )


def _load(path: Path) -> Verdict:
    d = json.loads(path.read_text(encoding="utf-8"))
    p = d.get("predicted", {})
    mol = MolInput(
        smiles=d["smiles"],
        predicted=PropPrediction(
            homo_ev=p.get("homo_ev"),
            lumo_ev=p.get("lumo_ev"),
            gap_ev=p.get("gap_ev"),
            dipole_debye=p.get("dipole_debye"),
        ),
        geometry_xyz=d.get("geometry_xyz"),
    )
    return apply_rules(mol)


def _sarif_from_fixture(path: Path) -> dict:
    v = _load(path)
    ref = InputRef(uri=path.name, molecule_id=None)
    return json.loads(to_sarif([v], [ref]))


@pytest.fixture(scope="module")
def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# AC-S1: el output valida contra el schema oficial 2.1.0
# ---------------------------------------------------------------------------
def test_sarif_valid_against_official_schema(schema):
    doc = _sarif_from_fixture(PKG_FIXTURES / "hallucinated.json")
    jsonschema.validate(instance=doc, schema=schema)  # levanta si inválido


# ---------------------------------------------------------------------------
# AC-S2: R1-R4 presentes en driver.rules con shortDescription no vacía
# ---------------------------------------------------------------------------
def test_driver_rules_present():
    doc = _sarif_from_fixture(PKG_FIXTURES / "hallucinated.json")
    rules = {r["id"]: r for r in doc["runs"][0]["tool"]["driver"]["rules"]}
    assert set(rules.keys()) == {"R1", "R2", "R3", "R4"}
    for rid, r in rules.items():
        assert r["name"]
        assert r["shortDescription"]["text"].strip()


# ---------------------------------------------------------------------------
# AC-S3: violación -> result con ruleId/level/message/locations a molécula
# ---------------------------------------------------------------------------
def test_result_maps_violation():
    doc = _sarif_from_fixture(PKG_FIXTURES / "hallucinated.json")
    results = doc["runs"][0]["results"]
    assert results, "debe haber al menos un result"
    for res in results:
        assert res["ruleId"] in {"R1", "R2", "R3", "R4"}
        assert res["level"] == "error"
        assert res["message"]["text"].strip()
        loc = res["locations"][0]["physicalLocation"]
        assert "moleculeId" in loc["properties"]
        assert "smiles" in loc["properties"]
        # DECISIÓN implícita en spec: NO hay region (línea/columna) porque el
        # input es una molécula, no código.
        assert "region" not in loc


# ---------------------------------------------------------------------------
# AC-S4: FAIL -> error; SKIP fuera de results
# hallucinated.json dispara R2 FAIL + R4 FAIL (R3_skipped no cuenta)
# ---------------------------------------------------------------------------
def test_skip_not_emitted():
    doc = _sarif_from_fixture(PKG_FIXTURES / "hallucinated.json")
    rule_ids = {r["ruleId"] for r in doc["runs"][0]["results"]}
    assert "R3" not in rule_ids  # R3 fue skipped -> no result
    assert "R2" in rule_ids and "R4" in rule_ids


# ---------------------------------------------------------------------------
# AC-S5: output parseable por consumidor genérico sin parser custom
# ---------------------------------------------------------------------------
def test_parseable_by_generic_consumer():
    raw = to_sarif(
        [_load(PKG_FIXTURES / "hallucinated.json")],
        [InputRef(uri="hallucinated.json")],
    )
    doc = json.loads(raw)  # cualquier consumidor puede hacer esto
    assert doc["runs"][0]["tool"]["driver"]["name"] == "qchem-leak-screen"
    assert isinstance(doc["runs"][0]["results"], list)


# ---------------------------------------------------------------------------
# AC-S6: 3 casos (PASS limpio / 1 violación / múltiples violaciones)
# ---------------------------------------------------------------------------
def test_pass_clean_zero_results():
    doc = _sarif_from_fixture(PKG_FIXTURES / "honest_water.json")
    assert doc["runs"][0]["results"] == []


def test_multiple_violations():
    doc = _sarif_from_fixture(PKG_FIXTURES / "hallucinated.json")
    rule_ids = {r["ruleId"] for r in doc["runs"][0]["results"]}
    # múltiples reglas distintas violadas a la vez (R2 + R4)
    assert rule_ids == {"R2", "R4"}


# ---------------------------------------------------------------------------
# DECISIÓN 2: versión del driver dinámica (no hardcodeada)
# ---------------------------------------------------------------------------
def test_driver_version_dynamic():
    import importlib.metadata

    doc = _sarif_from_fixture(PKG_FIXTURES / "honest_water.json")
    expected = importlib.metadata.version("qchem-leak-screen")
    assert doc["runs"][0]["tool"]["driver"]["version"] == expected


# ---------------------------------------------------------------------------
# Guarda: to_sarif exige inputs y verdicts de la misma longitud
# ---------------------------------------------------------------------------
def test_to_sarif_length_mismatch_raises():
    v = _load(PKG_FIXTURES / "honest_water.json")
    with pytest.raises(ValueError):
        to_sarif([v], [InputRef("a"), InputRef("b")])
