"""Render de veredictos a JSON, Markdown y SARIF 2.1.0."""

from __future__ import annotations

import json
from typing import List, Optional

from qchem_leak_screen.core.dataclasses import Verdict


# Metadatos de cada regla R1-R4 para el SARIF tool.driver.rules[].
# Texto derivado del README / RESEARCH.md existentes (no se inventa nada).
RULE_META: dict[str, tuple[str, str, str]] = {
    "R1": (
        "topology",
        "Valencia atómica, carga neta, aromaticidad (parser SMILES)",
        "R1 valida que el SMILES sea parseable y que la carga neta declarada sea "
        "coherente (una molécula pequeña no puede tener carga extrema salvo indicio "
        "de hallucinación estructural).",
    ),
    "R2": (
        "koopmans",
        "Consistencia gap ≈ -ε_HOMO y gap ≈ ε_LUMO - ε_HOMO (teorema de Koopmans)",
        "R2 aplica el teorema de Koopmans en aproximación de orbitales moleculares: "
        "el gap debe ser coherente con las energías HOMO/LUMO predichas.",
    ),
    "R3": (
        "symmetry",
        "Punto-grupo: dipolo nulo en grupos con inversión (skipped sin geometría)",
        "R3 requiere geometría 3D: si el punto-grupo tiene inversión, el momento "
        "dipolar debe ser 0. Sin geometría se marca skipped, no FAIL.",
    ),
    "R4": (
        "ranges",
        "Rangos físicos: gap > 0, dipolo en rango, sin NaN/inf",
        "R4 valida rangos físicos plausibles: aislante requiere gap > 0, el dipolo "
        "está en rango físico, y ninguna propiedad es NaN/inf.",
    ),
}

# Reglas que pueden aparecer como violación FAIL (las skipped no emiten result).
_FAIL_RULE_IDS = set(RULE_META.keys())


def _driver_version() -> str:
    """Versión del driver SARIF, dinámica desde el paquete instalado (DECISIÓN 2).

    No hardcodeada: se lee de los metadatos de instalación. Fallback a "0.1.0"
    si el paquete no está instalado (run suelto desde el árbol fuente).
    """
    try:
        from importlib.metadata import version

        return version("qchem-leak-screen")
    except Exception:  # pragma: no cover - depende del entorno de instalación
        return "0.1.0"


def to_json(verdicts: List[Verdict]) -> str:
    out = []
    for v in verdicts:
        out.append(
            {
                "smiles": v.smiles,
                "verdict": v.verdict,
                "violations": [
                    {"rule_id": x.rule_id, "severity": x.severity, "reason": x.reason}
                    for x in v.violations
                ],
            }
        )
    return json.dumps(out, indent=2, ensure_ascii=False)


def to_markdown(verdicts: List[Verdict]) -> str:
    lines = [
        "# qchem-leak-screen — reporte",
        "",
        "| SMILES | Veredicto | Reglas violadas |",
        "|--------|-----------|-----------------|",
    ]
    for v in verdicts:
        if not v.violations:
            viol = "—"
        else:
            viol = "; ".join(f"{x.rule_id}({x.severity}): {x.reason}" for x in v.violations)
        lines.append(f"| `{v.smiles}` | **{v.verdict}** | {viol} |")
    return "\n".join(lines) + "\n"


# Referencia de entrada para mapear SARIF locations (S024): el filtro opera sobre
# moléculas, no sobre código fuente, así que la "location" es el identificador de la
# molécula, no una línea de código.
class InputRef:
    """Identifica de dónde vino una molécula para el SARIF result.location.

    uri: ruta del archivo de entrada, o "--smiles" si fue inline.
    molecule_id: id estable de la molécula (input['id'] si existe, si no el SMILES).
    """

    def __init__(self, uri: str, molecule_id: Optional[str] = None) -> None:
        self.uri = uri
        self.molecule_id = molecule_id


def to_sarif(verdicts: List[Verdict], inputs: List[InputRef]) -> str:
    """Render SARIF 2.1.0 válido a partir de los veredictos (S020).

    - Cada regla R1-R4 => un entry en runs[0].tool.driver.rules[] (S021).
    - Cada violación FAIL => un result con ruleId, level="error",
      message.text = reason, y location apuntando a la molécula (S023, S024).
    - Las violaciones SKIP (p.ej. R3 sin geometría) NO emiten result (DECISIÓN 1).
    - Versión del driver dinámica vía importlib.metadata (DECISIÓN 2).
    """
    if len(inputs) != len(verdicts):
        raise ValueError("to_sarif: inputs y verdicts deben tener la misma longitud")

    driver_rules = []
    for rid in sorted(RULE_META.keys()):
        name, short, full = RULE_META[rid]
        driver_rules.append(
            {
                "id": rid,
                "name": name,
                "shortDescription": {"text": short},
                "fullDescription": {"text": full},
                "helpUri": "https://github.com/amurlaniakea/qchem-leak-screen#reglas-del-mvp",
            }
        )

    results = []
    for v, ref in zip(verdicts, inputs):
        mol_id = ref.molecule_id or v.smiles
        for viol in v.violations:
            # DECISIÓN 1: solo FAIL emite result; SKIP no.
            if viol.severity != "FAIL":
                continue
            results.append(
                {
                    "ruleId": viol.rule_id,
                    "level": "error",
                    "message": {"text": viol.reason},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": ref.uri},
                                "properties": {
                                    "moleculeId": mol_id,
                                    "smiles": v.smiles,
                                },
                            }
                        }
                    ],
                }
            )

    doc = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "qchem-leak-screen",
                        "version": _driver_version(),
                        "informationUri": "https://github.com/amurlaniakea/qchem-leak-screen",
                        "rules": driver_rules,
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(doc, indent=2, ensure_ascii=False)
