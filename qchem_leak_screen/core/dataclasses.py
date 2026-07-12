"""FUENTE UNICA de dataclasses para qchem-leak-screen.

Todos los modulos importan desde aqui. NUNCA se redefine MolInput/PropPrediction/
Verdict/RuleViolation en otro modulo (evita el bug de dataclass duplicado).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PropPrediction:
    """Propiedades cuanticas PREDICHAS por un modelo externo (no por este filtro)."""
    homo_ev: Optional[float] = None
    lumo_ev: Optional[float] = None
    gap_ev: Optional[float] = None
    dipole_debye: Optional[float] = None


@dataclass
class MolInput:
    """Entrada del filtro: SMILES + props predichas + geometria 3D opcional."""
    smiles: str
    predicted: PropPrediction
    geometry_xyz: Optional[str] = None


@dataclass
class RuleViolation:
    """Una regla fisica violada (o skipped por falta de dato)."""
    rule_id: str          # "R1".."R4" | "R3_skipped"
    severity: str         # "FAIL" | "SKIP"
    reason: str


@dataclass
class Verdict:
    """Veredicto agregado para una molecula."""
    smiles: str
    verdict: str                       # "PASS" | "FAIL"
    violations: list[RuleViolation] = field(default_factory=list)

    def add(self, v: RuleViolation) -> None:
        self.violations.append(v)

    def finalize(self) -> None:
        self.verdict = "FAIL" if any(v.severity == "FAIL" for v in self.violations) else "PASS"
