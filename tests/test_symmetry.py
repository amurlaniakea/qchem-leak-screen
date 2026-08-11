# SPDX-FileCopyrightText: 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

from qchem_leak_screen.core.dataclasses import MolInput, PropPrediction
from qchem_leak_screen.core.symmetry import check_symmetry


def test_r3_skipped_without_geometry():
    v = check_symmetry(MolInput(smiles="O", predicted=PropPrediction(dipole_debye=1.85)))
    assert v is not None and v.rule_id == "R3_skipped" and v.severity == "SKIP"


def test_r3_inversion_group_with_dipole_fail():
    # O2 centrosimetrico (dos atomos en x y -x), pero dipolo != 0 => violacion
    xyz = "2\n\nO 0.6 0.0 0.0\nO -0.6 0.0 0.0\n"
    v = check_symmetry(
        MolInput(smiles="O=O", predicted=PropPrediction(dipole_debye=1.5), geometry_xyz=xyz)
    )
    assert v is not None and v.rule_id == "R3" and v.severity == "FAIL"
    assert "dipole_in_inversion_group" in v.reason, v.reason


def test_r3_inversion_group_zero_dipole_ok():
    xyz = "2\n\nO 0.6 0.0 0.0\nO -0.6 0.0 0.0\n"
    v = check_symmetry(
        MolInput(smiles="O=O", predicted=PropPrediction(dipole_debye=0.0), geometry_xyz=xyz)
    )
    assert v is None, v
