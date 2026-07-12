"""CLI de qchem-leak-screen.

Uso:
  qls check --in <archivo.json | directorio> [--format json|md]
  qls check --smiles "O" --props '{"homo_ev":-12.6,...}'

Las reglas son puras y no invocan NINGUN modelo externo (agnostico de modelo).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

import typer

from qchem_leak_screen.core.dataclasses import MolInput, PropPrediction, Verdict
from qchem_leak_screen.core.report import to_json, to_markdown
from qchem_leak_screen.core.rules import apply_rules

app = typer.Typer(help="Filtro perimetral de sanity fisico para props cuanticas predichas por IA")


@app.callback()
def _root() -> None:
    """Filtro perimetral de sanity fisico para props cuanticas predichas por IA."""


def _load_one(path: Path) -> MolInput:
    data = json.loads(path.read_text(encoding="utf-8"))
    pred = data.get("predicted", {})
    return MolInput(
        smiles=data["smiles"],
        predicted=PropPrediction(
            homo_ev=pred.get("homo_ev"),
            lumo_ev=pred.get("lumo_ev"),
            gap_ev=pred.get("gap_ev"),
            dipole_debye=pred.get("dipole_debye"),
        ),
        geometry_xyz=data.get("geometry_xyz"),
    )


def _load_inputs(in_path: Path, smiles: str | None, props: str | None) -> List[MolInput]:
    if smiles is not None and props is not None:
        pred = json.loads(props)
        return [MolInput(
            smiles=smiles,
            predicted=PropPrediction(
                homo_ev=pred.get("homo_ev"),
                lumo_ev=pred.get("lumo_ev"),
                gap_ev=pred.get("gap_ev"),
                dipole_debye=pred.get("dipole_debye"),
            ),
        )]
    if not in_path:
        raise typer.BadParameter("Usa --in <archivo|dir> o --smiles + --props")
    if in_path.is_dir():
        return [_load_one(p) for p in sorted(in_path.glob("*.json"))]
    return [_load_one(in_path)]


@app.command()
def check(
    in_path: Path = typer.Option(None, "--in", help="archivo JSON o directorio"),
    format: str = typer.Option("json", "--format", help="json | md"),
    smiles: str = typer.Option(None, "--smiles", help="SMILES inline"),
    props: str = typer.Option(None, "--props", help="JSON de props predichas inline"),
):
    """Filtra propiedades cuanticas predichas por IA contra leyes fisicas."""
    try:
        mols = _load_inputs(in_path, smiles, props)
    except (json.JSONDecodeError, KeyError, typer.BadParameter) as e:
        typer.echo(f"ERROR de entrada: {e}", err=True)
        raise typer.Exit(code=2)

    verdicts: List[Verdict] = [apply_rules(m) for m in mols]
    out = to_json(verdicts) if format == "json" else to_markdown(verdicts)
    typer.echo(out)

    if any(v.verdict == "FAIL" for v in verdicts):
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


def main():
    app()


if __name__ == "__main__":
    main()
