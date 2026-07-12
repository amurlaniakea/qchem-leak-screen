"""Registry de reglas y orquestador apply_rules().

Cada regla es una funcion pura (MolInput) -> Optional[RuleViolation].
apply_rules recorre el registro, aplica las reglas cuyos datos esten presentes,
agrega las violaciones y finaliza el veredicto (PASS/FAIL).
"""

from __future__ import annotations

from typing import Callable, List, Optional

from qchem_leak_screen.core.dataclasses import MolInput, RuleViolation, Verdict
from qchem_leak_screen.core.koopmans import check_koopmans
from qchem_leak_screen.core.ranges import check_ranges
from qchem_leak_screen.core.symmetry import check_symmetry
from qchem_leak_screen.core.topology import check_topology

# Orden estable: R1..R4
RULES: List[Callable[[MolInput], Optional[RuleViolation]]] = [
    check_topology,  # R1
    check_koopmans,  # R2
    check_symmetry,  # R3
    check_ranges,  # R4
]


def apply_rules(mol: MolInput) -> Verdict:
    v = Verdict(smiles=mol.smiles, verdict="PASS")
    for rule in RULES:
        viol = rule(mol)
        if viol is not None:
            v.add(viol)
    v.finalize()
    return v
