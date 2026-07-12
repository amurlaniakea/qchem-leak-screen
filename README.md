# qchem-leak-screen

Filtro perimetral de *sanity* físico para propiedades cuánticas predichas por IA.

Los modelos generativos/predictivos de moléculas pequeñas predicen propiedades
cuánticas (momento dipolar, energías HOMO/LUMO, brecha de banda) en milisegundos
sin correr DFT. Pero nadie valida que esas propiedades cumplan leyes físicas.
`qchem-leak-screen` es un *linter* químico agnóstico del modelo: recibe
`(SMILES, propiedades_predichas)` y emite un veredicto por regla física dura,
con motivo. Todo en CPU, sin GPU, sin llamar a ningún modelo.

## Licencia

AGPL-3.0-or-later — Copyright (C) 2026 Pedro Sordo Martínez — amurlaniakea@gmail.com

## Instalación

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Uso

```bash
# una molécula desde archivo
qls check --in fixtures/honest_water.json --format json

# un directorio de fixtures
qls check --in fixtures/ --format markdown

# inline
qls check --smiles "O" --props '{"homo_ev":-12.6,"lumo_ev":-1.2,"gap_ev":11.4,"dipole_debye":1.85}'
```

Códigos de salida: `0` = OK (veredicto emitido), `1` = hallazgo (FAIL),
`2` = error de entrada.

## Reglas del MVP

- **R1 Topología**: valencia atómica, carga neta, aromaticidad (parser SMILES).
- **R2 Koopmans**: consistencia `gap ≈ -ε_HOMO` y `gap ≈ ε_LUMO − ε_HOMO`.
- **R3 Simetría / punto-grupo**: si hay geometría 3D, el dipolo debe ser 0 en
  grupos con inversión (skipped sin geometría).
- **R4 Rangos físicos**: gap > 0 para aislante, dipolo en rango, sin NaN/inf.

## Estado

MVP — ver `spec/` (SDD).
