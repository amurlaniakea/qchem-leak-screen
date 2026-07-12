"""R3 - Simetria / punto-grupo: si hay geometria 3D y el grupo tiene inversion,
el momento dipolar debe ser 0.

Implementacion minima del MVP:
  - Parsea geometry_xyz a coords.
  - Detecta centro de inversion: para cada atomo en (x,y,z) debe existir otro en
    (-x,-y,-z) (dentro de tolerancia). Si se cumple => grupo con inversion.
  - Si grupo con inversion y dipole_debye != 0 (con tolerancia) => violacion.
  - SIN geometria => R3_skipped (nunca FAIL por falta de dato).
"""

from __future__ import annotations

from qchem_leak_screen.core.dataclasses import MolInput, RuleViolation

DIP_TOL_DEBYE: float = 0.1
INVERSION_TOL: float = 0.25


def _parse_xyz(xyz: str):
    coords = []
    for line in xyz.strip().splitlines():
        parts = line.split()
        if len(parts) >= 4:
            try:
                coords.append(tuple(float(x) for x in parts[1:4]))
            except ValueError:
                continue
    return coords


def _has_inversion_center(coords) -> bool:
    if not coords:
        return False
    s = set(coords)
    for x, y, z in coords:
        if not any(
            abs(-x - ox) < INVERSION_TOL
            and abs(-y - oy) < INVERSION_TOL
            and abs(-z - oz) < INVERSION_TOL
            for (ox, oy, oz) in s
        ):
            return False
    return True


def check_symmetry(mol: MolInput) -> RuleViolation | None:
    if not mol.geometry_xyz:
        return RuleViolation(
            rule_id="R3_skipped",
            severity="SKIP",
            reason="no_geometry: R3 requiere geometria 3D; omitida",
        )
    coords = _parse_xyz(mol.geometry_xyz)
    if not coords:
        return RuleViolation(
            rule_id="R3_skipped",
            severity="SKIP",
            reason="no_geometry: geometria no parseable; omitida",
        )
    if _has_inversion_center(coords):
        d = mol.predicted.dipole_debye
        if d is not None and abs(d) > DIP_TOL_DEBYE:
            return RuleViolation(
                rule_id="R3",
                severity="FAIL",
                reason=f"dipole_in_inversion_group: grupo con inversion pero dipole={d} D != 0",
            )
    return None
