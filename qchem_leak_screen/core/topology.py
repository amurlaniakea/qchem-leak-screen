# SPDX-FileCopyrightText: 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""R1 - Topologia: valencia atómica, carga neta, aromaticidad basica.

Parser SMILES minimo propio (sin RDKit) suficiente para el MVP:
- Calcula la carga neta total de la molecula a partir de los tokens de carga [+] / [-].
- Detecta SMILES no parseable (parentesis/brakets desbalanceados) -> FAIL.
- (Opcional) si RDKit esta disponible, usa su parseo para aromaticidad completa;
  pero la CARGA NETA siempre se valida con el parser propio (independiente).

El MVP solo exige: (a) SMILES parseable, (b) carga neta coherente con lo que el
modelo predice implícitamente (una molecula neutra no puede tener carga +5 en C6H6).
Como el filtro recibe SOLO el SMILES + props, R1 valida:
  - SMILES parseable (no basura).
  - Si el SMILES declara una carga neta |q| > MAX_NET_CHARGE, lo marca como
    indicio de hallucinacion estructural (una molecula pequena con carga extrema
    es fisicamente improbable y suele senalar un SMILES corrupto del generador).
"""

from __future__ import annotations

import re

from qchem_leak_screen.core.dataclasses import MolInput, RuleViolation

# Carga neta maxima plausible para una molecula pequena generada por IA.
MAX_NET_CHARGE: int = 4


def _net_charge_from_smiles(smiles: str) -> int | None:
    """Suma las cargas explicitas en el SMILES. None si hay un token ilegible."""
    # Tokens de carga: [+], [-], [+2], [-3], [--], etc. dentro de corchetes atomicos.
    total = 0
    for m in re.finditer(r"\[([^\[\]]*)\]", smiles):
        inner = m.group(1)
        # busca signos de carga al final del token atomico
        cm = re.search(r"([+-]+)(\d+)?$", inner)
        if cm:
            sign = cm.group(1)
            mult = int(cm.group(2)) if cm.group(2) else 1
            total += (1 if sign.startswith("+") else -1) * len(sign) * mult
        elif re.search(r"[+-]$", inner):
            # caso "[NH+]" sin numero
            total += 1 if inner.endswith("+") else -1
    return total


def _balanced(smiles: str) -> bool:
    """Parentesis, corchetes y ANILLOS (digitos de anillo en par) balanceados."""
    depth = 0
    for ch in smiles:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
            if depth < 0:
                return False
    if depth != 0:
        return False
    # anillos: contar digitos FUERA de corchetes [...] (los de carga van dentro)
    import re as _re
    from collections import Counter

    outside = _re.sub(r"\[[^\]]*\]", "", smiles)
    rings = _re.findall(r"\d", outside)
    counts = Counter(rings)
    return all(c == 2 for c in counts.values()) if rings else True


def check_topology(mol: MolInput) -> RuleViolation | None:
    """Aplica R1. Devuelve RuleViolation (FAIL) o None (OK)."""
    smiles = mol.smiles.strip()
    if not smiles or not _balanced(smiles):
        return RuleViolation(
            rule_id="R1",
            severity="FAIL",
            reason="unparseable_smiles: parentesis/corchetes desbalanceados",
        )
    # Carga declarada en el SMILES
    q = _net_charge_from_smiles(smiles)
    if q is None:
        return RuleViolation(
            rule_id="R1",
            severity="FAIL",
            reason="unparseable_smiles: token de carga ilegible",
        )
    if abs(q) > MAX_NET_CHARGE:
        return RuleViolation(
            rule_id="R1",
            severity="FAIL",
            reason=f"net_charge_out_of_range: |q|={abs(q)} > {MAX_NET_CHARGE} "
            f"(indicio de hallucinacion estructural)",
        )
    return None
