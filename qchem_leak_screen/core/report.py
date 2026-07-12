"""Render de veredictos a JSON y Markdown."""
from __future__ import annotations

import json
from typing import List

from qchem_leak_screen.core.dataclasses import Verdict


def to_json(verdicts: List[Verdict]) -> str:
    out = []
    for v in verdicts:
        out.append({
            "smiles": v.smiles,
            "verdict": v.verdict,
            "violations": [
                {"rule_id": x.rule_id, "severity": x.severity, "reason": x.reason}
                for x in v.violations
            ],
        })
    return json.dumps(out, indent=2, ensure_ascii=False)


def to_markdown(verdicts: List[Verdict]) -> str:
    lines = ["# qchem-leak-screen — reporte", "",
             "| SMILES | Veredicto | Reglas violadas |",
             "|--------|-----------|-----------------|"]
    for v in verdicts:
        if not v.violations:
            viol = "—"
        else:
            viol = "; ".join(f"{x.rule_id}({x.severity}): {x.reason}" for x in v.violations)
        lines.append(f"| `{v.smiles}` | **{v.verdict}** | {viol} |")
    return "\n".join(lines) + "\n"
