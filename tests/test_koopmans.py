# SPDX-FileCopyrightText: 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

from qchem_leak_screen.core.dataclasses import MolInput, PropPrediction
from qchem_leak_screen.core.koopmans import check_koopmans


def _mol(**kw):
    return MolInput(smiles="CCO", predicted=PropPrediction(**kw))


def test_r2_water_ok():
    v = check_koopmans(_mol(homo_ev=-12.6, lumo_ev=-1.2, gap_ev=11.4))
    assert v is None, v


def test_r2_negative_gap_fail():
    v = check_koopmans(_mol(homo_ev=-3.0, lumo_ev=-1.0, gap_ev=-2.0))
    assert v is not None and v.rule_id == "R2" and v.severity == "FAIL"
    assert "negative_gap" in v.reason, v.reason


def test_r2_koopmans_mismatch_fail():
    # gap no coincide con -homo dentro de la tolerancia
    v = check_koopmans(_mol(homo_ev=-12.6, gap_ev=2.0))
    assert v is not None and v.rule_id == "R2"
    assert "koopmans_gap_mismatch" in v.reason, v.reason
