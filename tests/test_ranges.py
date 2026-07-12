import math

from qchem_leak_screen.core.dataclasses import MolInput, PropPrediction
from qchem_leak_screen.core.ranges import check_ranges


def _mol(**kw):
    return MolInput(smiles="O", predicted=PropPrediction(**kw))


def test_r4_water_ok():
    v = check_ranges(_mol(homo_ev=-12.6, lumo_ev=-1.2, gap_ev=11.4, dipole_debye=1.85))
    assert v is None, v


def test_r4_dipole_out_of_range_fail():
    v = check_ranges(_mol(dipole_debye=999.0))
    assert v is not None and v.rule_id == "R4" and v.severity == "FAIL"
    assert "dipole_out_of_range" in v.reason, v.reason


def test_r4_nan_fail():
    v = check_ranges(_mol(gap_ev=float("nan")))
    assert v is not None and v.rule_id == "R4"
    assert "non_finite" in v.reason, v.reason


def test_r4_gap_nonpositive_fail():
    v = check_ranges(_mol(gap_ev=0.0))
    assert v is not None and v.rule_id == "R4"
    assert "gap_nonpositive" in v.reason, v.reason
