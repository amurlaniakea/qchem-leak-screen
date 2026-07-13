# RESEARCH — qchem-leak-screen

Documento de transparencia metodológica. Complementa `spec/` (SDD). El objetivo es
el mismo que en cryoval/RNAValidate: dejar por escrito, sin ambigüedad, qué es y qué
**no es** esta herramienta, y sobre qué evidencia se apoya.

## Tesis del proyecto

Los modelos de *property-prediction* (y los generativos que los usan de oráculo)
escupen propiedades cuánticas — momento dipolar, energías HOMO/LUMO, brecha de
banda — en milisegundos, sin correr DFT. Ninguno valida que la propiedad *predicha*
cumpla leyes físicas. Antes de mandar un candidato a síntesis o a un DFT caro, conviene
filtrar los "milagros" que violan Koopmans, rompen la simetría de punto-grupo o tienen
topología imposible.

**El gap:** no existe una herramienta OSS reutilizable que haga ese sanity-check
perimetral de forma agnóstica al modelo. No es que falte un *cálculo* mejor — es que
falta la capa de *control* que revisa lo que otro modelo ya predijo.

## Evidencia del gap (auditoría 2026-07-12)

- **Señal de GitHub (2026-07-12):** búsquedas `quantum chemical property validation ML`
  = 0, `molecular property physical consistency` = 0, `Koopmans theorem ML prediction` = 0,
  `molecule property sanity check ML` = 0. `topic:quantum-chemistry` = 906 (deepchem 6860★,
  OpenFermion 1709★) = ecosistema de **cálculo**, cero sanity-check.
- **Auditoría a nivel de código fuente (2026-07-12):**
  - `deepchem/utils/dft_utils/hamilton/intor/symmetry.py` define `BaseSymmetry` para
    cálculo DFT *interno* (`get_reduced_shape` / `reconstruct_array`), **no** un validador
    de salida.
  - `deepchem/molnet/check_availability.py` = disponibilidad de datasets MolNet.
  - Árbol de OpenFermion = 0 archivos con `valid` / `consist` / `sanity` / `koopmans`.
  - Conclusión: ambos son **motores de cálculo**, no *linters*. El gap se sostiene a
    nivel de código, no solo de búsqueda.

## Las reglas son físicamente derivadas, no ajustadas al fixture

- **R2 (Koopmans):** `gap ≈ −ε_HOMO` en aproximación de orbitales moleculares
  (Koopmans, 1934). Es una relación física, no un umbral tuneado.
- **R3 (simetría):** un momento dipolar distinto de cero en un grupo con inversión
  (Ci, C2h, D2h, Oh…) viola la simetría centrosimétrica. Relación de teoría de grupos
  (Cotton).
- **R4 (rangos):** un aislante estable tiene `gap > 0`; el dipolo molecular conocido
  rara vez supera ~15 D. Umbrales documentados en `core/constants.py` como
  `TOL_KOOPMANS_EV` y `DIP_MAX_DEBYE`.

## Nota de validación AC-6 (external-validity)

Las reglas **no fueron validadas contra un benchmark experimental propio**. Son
**físicamente derivadas** a partir de leyes conocidas. Para evitar *circularidad* en
los tests:

- Los fixtures `honest_water.json` / `honest_ethanol.json` usan valores de
  **literatura / DFT reales** (no generados por las reglas del filtro).
- El fixture `hallucinated.json` usa valores **manifiestamente imposibles**
  (gap negativo, dipolo 999 D, carga neta +5 en C6H6).

Ningún fixture se construye con las propias reglas del chequeador. Esto prueba que el
código detecta anomalías reales, no solo que "no tiene bugs".

## Referencias

- Koopmans, T. *Über die Zuordnung von Wellenfunktionen und Eigenwerten zu den
  Einzelnen Elektronen eines Atoms*, Physica **1**, 104–113 (1934). — base de R2
  (`gap ≈ −ε_HOMO`).
- Cotton, F. A. *Chemical Applications of Group Theory*. Wiley. — base de R3
  (punto-grupo, centros de inversión, momento dipolar nulo).
- arXiv:2606.30961 — ElemeNet (property prediction en ms sin DFT).
- arXiv:2603.27106 — ADEPT-PolyGraphMT (property prediction / conformeros).
- arXiv:2606.08825 — estudio de ensembles de conformeros (property prediction).

## Qué NO es esta herramienta

- No es un calculador DFT ni un solver de estructura electrónica.
- No entrena ni invoca modelos generativos (es perimetral y agnóstico).
- No garantiza que una molécula "PASS" exista, sea estable más allá de estas leyes,
  ni que sus propiedades sean las correctas — solo que no violan R1–R4.
- No sustituye la validación experimental ni un cálculo *ab initio* de referencia.

## Salida SARIF (Fase 2, feature 002)

Además de JSON/Markdown, el filtro puede emitir **SARIF 2.1.0** (`--format sarif`),
consumible por GitHub Code Scanning sin parser custom. Es **render puro** del
`Verdict` ya existente: no añade lógica de validación ni cambia R1–R4. Cada regla es
un `rule` SARIF; cada violación, un `result` con `level="error"` y el `reason` como
`message.text`. Las reglas *skipped* no se emiten como hallazgo. Es transparencia de
formato, no nueva autoridad física.

---

*Documento vivo — actualizar al añadir reglas (Fase 2+) o benchmarks experimentales.*
