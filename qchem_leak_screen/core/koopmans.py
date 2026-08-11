# SPDX-FileCopyrightText: 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""R2 - Koopmans: consistencia de las energias de orbitales predichas.

Teorema de Koopmans (aproximacion de orbitales moleculares): el gap de ionizacion
aprox. -epsilon_HOMO. En terminos de las props predichas:
  (a) gap_ev  ~= -homo_ev
  (b) gap_ev  ~= lumo_ev - homo_ev
Si el modelo da gap negativo, la molecula no es un aislante estable (banda
conduccion invertida) => hallucinacion o leakage.
"""

from __future__ import annotations

from qchem_leak_screen.core.constants import TOL_KOOPMANS_EV
from qchem_leak_screen.core.dataclasses import MolInput, RuleViolation


def check_koopmans(mol: MolInput) -> RuleViolation | None:
    p = mol.predicted
    # (a) gap negativo => aislante inestable
    if p.gap_ev is not None and p.gap_ev < 0:
        return RuleViolation(
            rule_id="R2",
            severity="FAIL",
            reason=f"negative_gap: gap_ev={p.gap_ev} < 0 (no es aislante estable)",
        )
    # (b) consistencia gap vs -homo
    if p.gap_ev is not None and p.homo_ev is not None:
        if abs(p.gap_ev - (-p.homo_ev)) > TOL_KOOPMANS_EV:
            return RuleViolation(
                rule_id="R2",
                severity="FAIL",
                reason=f"koopmans_gap_mismatch: |gap - (-homo)|="
                f"{abs(p.gap_ev - (-p.homo_ev)):.2f} eV > tol {TOL_KOOPMANS_EV}",
            )
    # (c) consistencia gap vs (lumo - homo)
    if p.gap_ev is not None and p.lumo_ev is not None and p.homo_ev is not None:
        if abs(p.gap_ev - (p.lumo_ev - p.homo_ev)) > TOL_KOOPMANS_EV:
            return RuleViolation(
                rule_id="R2",
                severity="FAIL",
                reason=f"gap_lumo_homo_mismatch: |gap - (lumo-homo)|="
                f"{abs(p.gap_ev - (p.lumo_ev - p.homo_ev)):.2f} eV > tol {TOL_KOOPMANS_EV}",
            )
    return None
