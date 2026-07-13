"""CLI de qchem-leak-screen.

Uso:
  qls check --in <archivo.json | directorio> [--format json|md]
  qls check --smiles "O" --props '{"homo_ev":-12.6,...}'

Las reglas son puras y no invocan NINGUN modelo externo (agnostico de modelo).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import typer

from qchem_leak_screen.core.dataclasses import MolInput, PropPrediction, Verdict
from qchem_leak_screen.core.report import to_json, to_markdown, to_sarif, InputRef
from qchem_leak_screen.core.rules import apply_rules

app = typer.Typer(help="Filtro perimetral de sanity fisico para props cuanticas predichas por IA")


@app.callback()
def _root() -> None:
    """Filtro perimetral de sanity fisico para props cuanticas predichas por IA."""


def _load_one(path: Path) -> tuple[MolInput, InputRef]:
    data = json.loads(path.read_text(encoding="utf-8"))
    pred = data.get("predicted", {})
    mol = MolInput(
        smiles=data["smiles"],
        predicted=PropPrediction(
            homo_ev=pred.get("homo_ev"),
            lumo_ev=pred.get("lumo_ev"),
            gap_ev=pred.get("gap_ev"),
            dipole_debye=pred.get("dipole_debye"),
        ),
        geometry_xyz=data.get("geometry_xyz"),
    )
    ref = InputRef(uri=path.name, molecule_id=data.get("id"))
    return mol, ref


def _load_inputs(
    in_path: Path, smiles: str | None, props: str | None
) -> tuple[List[MolInput], List[InputRef]]:
    if smiles is not None and props is not None:
        pred = json.loads(props)
        mol = MolInput(
            smiles=smiles,
            predicted=PropPrediction(
                homo_ev=pred.get("homo_ev"),
                lumo_ev=pred.get("lumo_ev"),
                gap_ev=pred.get("gap_ev"),
                dipole_debye=pred.get("dipole_debye"),
            ),
        )
        ref = InputRef(uri="--smiles", molecule_id=None)
        return [mol], [ref]
    if not in_path:
        raise typer.BadParameter("Usa --in <archivo|dir> o --smiles + --props")
    if in_path.is_dir():
        pairs = [_load_one(p) for p in sorted(in_path.glob("*.json"))]
    else:
        pairs = [_load_one(in_path)]
    mols = [m for m, _ in pairs]
    refs = [r for _, r in pairs]
    return mols, refs


@app.command()
def check(
    in_path: Path = typer.Option(None, "--in", help="archivo JSON o directorio"),
    format: str = typer.Option("json", "--format", help="json | md | sarif"),
    smiles: str = typer.Option(None, "--smiles", help="SMILES inline"),
    props: str = typer.Option(None, "--props", help="JSON de props predichas inline"),
):
    """Filtra propiedades cuanticas predichas por IA contra leyes fisicas."""
    try:
        mols, refs = _load_inputs(in_path, smiles, props)
    except (json.JSONDecodeError, KeyError, typer.BadParameter) as e:
        typer.echo(f"ERROR de entrada: {e}", err=True)
        raise typer.Exit(code=2)

    verdicts: List[Verdict] = [apply_rules(m) for m in mols]
    if format == "sarif":
        out = to_sarif(verdicts, refs)
    elif format == "md":
        out = to_markdown(verdicts)
    else:
        out = to_json(verdicts)
    typer.echo(out)

    if any(v.verdict == "FAIL" for v in verdicts):
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


def main():
    app()


if __name__ == "__main__":
    main()
