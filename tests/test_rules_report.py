# SPDX-FileCopyrightText: 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

from qchem_leak_screen.core.dataclasses import MolInput, PropPrediction, Verdict
from qchem_leak_screen.core.report import to_json, to_markdown
from qchem_leak_screen.core.rules import apply_rules


def test_apply_rules_water_pass():
    v = apply_rules(
        MolInput(
            smiles="O",
            predicted=PropPrediction(homo_ev=-12.6, lumo_ev=-1.2, gap_ev=11.4, dipole_debye=1.85),
        )
    )
    assert isinstance(v, Verdict)
    assert v.verdict == "PASS"
    # R3 skipped (sin geometria) pero no FAIL
    assert all(x.severity != "FAIL" for x in v.violations)


def test_apply_rules_hallucinated_fail():
    v = apply_rules(
        MolInput(
            smiles="c1ccccc1",
            predicted=PropPrediction(homo_ev=-3.0, lumo_ev=-1.0, gap_ev=-2.0, dipole_debye=999.0),
        )
    )
    assert v.verdict == "FAIL"
    ids = {x.rule_id for x in v.violations}
    assert "R2" in ids and "R4" in ids


def test_report_json_keys():
    v = apply_rules(MolInput(smiles="O", predicted=PropPrediction(gap_ev=11.4)))
    out = to_json([v])
    assert '"smiles"' in out and '"verdict"' in out and '"violations"' in out


def test_report_markdown_table():
    v = apply_rules(MolInput(smiles="O", predicted=PropPrediction(gap_ev=11.4)))
    md = to_markdown([v])
    assert "# qchem-leak-screen" in md
    assert "| `O` |" in md
