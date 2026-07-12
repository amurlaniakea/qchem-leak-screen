# qchem-leak-screen

[![License: AGPL-3.0-or-later](https://img.shields.io/badge/License-AGPL--3.0--or--later-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

Filtro perimetral de *sanity* físico para propiedades cuánticas predichas por IA.

Los modelos generativos/predictivos de moléculas pequeñas predicen propiedades
cuánticas (momento dipolar, energías HOMO/LUMO, brecha de banda) en milisegundos
sin correr DFT. Pero nadie valida que esas propiedades cumplan leyes físicas.
`qchem-leak-screen` es un *linter* químico agnóstico del modelo: recibe
`(SMILES, propiedades_predichas)` y emite un veredicto por regla física dura,
con motivo. Todo en CPU, sin GPU, sin llamar a ningún modelo.

## Features

- **Agnóstico del modelo generativo**: el filtro solo lee un JSON que *tú* produces
  con tu modelo; no importa ni invoca ningún modelo externo (anti-oráculo).
- **CPU-only, sin GPU, sin DFT**: heurísticas físicas puras, <50 ms por molécula.
- **Veredicto con motivo, no score ciego**: cada violación lleva `rule_id`,
  `severity` y `reason` explícitos.
- **Reglas R1–R4** (ver abajo) cubriendo topología, teorema de Koopmans, simetría de
  punto-grupo y rangos físicos plausibles.
- **Reportes JSON y Markdown** imprimibles a stdout sin ejecutar cómputo caro.
- **Modo dry-run / fixtures** con *ground truth* independiente de las reglas
  (valores de literatura/DFT reales y valores manifiestamente imposibles).

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

## Limitaciones / Honestidad metodológica

`qchem-leak-screen` es una herramienta de **sanity-check heurístico**, no una
autoridad de química cuántica. Esto es deliberado y debe ser así:

- **R1–R4 son heurísticas físicas de detección de anomalías, NO verdad absoluta.**
  Aplican leyes físicas *conocidas* (Koopmans, simetría de punto-grupo, topología)
  para señalar propiedades que violan lo físicamente posible. Un veredicto PASS no
  prueba que la molécula exista ni que las propiedades sean correctas; solo que no
  violan esas leyes duras.
- **El filtro NUNCA calcula química cuántica real.** No corre DFT (ORCA, Gaussian,
  PySCF) ni ningún solver. Solo inspecciona valores *ya predichos por otro modelo*
  y reporta contradicciones con leyes físicas. No es un sustituto de un cálculo DFT.
- **Las tolerancias (p. ej. `TOL_KOOPMANS`, `DIP_MAX`) son físicamente derivadas**,
  no ajustadas hasta que el fixture "pase". Koopmans es una aproximación y el DFT
  real desvía ~1–2 eV; por eso la tolerancia es generosa y documentada en
  `core/constants.py`.
- **Cobertura de "hallucination" parcial.** R3 requiere geometría 3D; sin ella se
  marca como `skipped`, no como FAIL. Una molécula puede pasar el filtro y seguir
  siendo químicamente inviable por motivos que estas cuatro reglas no cubren.
- **Validación (AC-6, external-validity).** Los fixtures usan *ground truth*
  independiente de las reglas (valores de literatura/DFT reales y valores
  manifiestamente imposibles). Las reglas NO fueron validadas contra un benchmark
  experimental propio; son físicamente derivadas. Véase `RESEARCH.md`.

## Estado

MVP — ver `spec/` (SDD).
