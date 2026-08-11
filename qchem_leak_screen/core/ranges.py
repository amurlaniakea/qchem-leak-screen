# SPDX-FileCopyrightText: 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""R4 - Rangos fisicos plausibles: gap > 0 para aislante, dipolo en rango, sin NaN/inf."""

from __future__ import annotations

import math

from qchem_leak_screen.core.constants import DIP_MAX_DEBYE
from qchem_leak_screen.core.dataclasses import MolInput, RuleViolation


def check_ranges(mol: MolInput) -> RuleViolation | None:
    p = mol.predicted
    # NaN / inf en cualquier prop => rango invalido
    for name, val in (
        ("homo_ev", p.homo_ev),
        ("lumo_ev", p.lumo_ev),
        ("gap_ev", p.gap_ev),
        ("dipole_debye", p.dipole_debye),
    ):
        if val is not None and (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
            return RuleViolation(
                rule_id="R4",
                severity="FAIL",
                reason=f"non_finite_{name}: valor {val} no es finito",
            )
    # gap <= 0 para un aislante => rango invalido (mismo chequeo de signo que R2,
    # pero aqui por rango fisico de aislante, no por Koopmans)
    if p.gap_ev is not None and p.gap_ev <= 0:
        return RuleViolation(
            rule_id="R4",
            severity="FAIL",
            reason=f"gap_nonpositive: gap_ev={p.gap_ev} <= 0 (aislante requiere gap > 0)",
        )
    # dipolo fuera de rango de sanidad
    if p.dipole_debye is not None and (p.dipole_debye < 0 or p.dipole_debye > DIP_MAX_DEBYE):
        return RuleViolation(
            rule_id="R4",
            severity="FAIL",
            reason=f"dipole_out_of_range: dipole={p.dipole_debye} D fuera de [0, {DIP_MAX_DEBYE}]",
        )
    return None
