import json
import subprocess
import sys
from pathlib import Path

FIX = Path(__file__).resolve().parent.parent / "qchem_leak_screen" / "fixtures"
CLI = [sys.executable, "-m", "qchem_leak_screen.cli"]


def _run(args):
    return subprocess.run(CLI + args, capture_output=True, text=True)


def test_e1_honest_water_pass_and_keys():
    r = _run(["check", "--in", str(FIX / "honest_water.json"), "--format", "json"])
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert isinstance(data, list) and len(data) == 1
    d = data[0]
    # claves exactas exigidas por AC-1
    assert set(d.keys()) >= {"smiles", "verdict", "violations"}
    assert d["smiles"] == "O"
    assert d["verdict"] == "PASS"
    # violaciones FAIL vacias (los SKIP de R3 no cuentan como fallo)
    assert all(v["severity"] != "FAIL" for v in d["violations"])


def test_e2_hallucinated_fail_with_violations():
    r = _run(["check", "--in", str(FIX / "hallucinated.json"), "--format", "json"])
    # codigo 1 = hallazgo (FAIL)
    assert r.returncode == 1, r.stdout
    data = json.loads(r.stdout)
    d = data[0]
    assert d["verdict"] == "FAIL"
    rule_ids = {v["rule_id"] for v in d["violations"]}
    # external-validity: el fixture imposible debe disparar R1-R4
    assert "R2" in rule_ids, rule_ids  # gap negativo
    assert "R4" in rule_ids, rule_ids  # dipolo 999 fuera de rango
    # razon de cada violacion presente
    for v in d["violations"]:
        assert v["reason"]


def test_e2_ethanol_pass():
    r = _run(["check", "--in", str(FIX / "honest_ethanol.json"), "--format", "json"])
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)[0]
    assert d["verdict"] == "PASS"


def test_markdown_report_prints_without_gpu():
    r = _run(["check", "--in", str(FIX), "--format", "md"])
    assert r.returncode == 1  # al menos hallucinated falla
    assert "# qchem-leak-screen" in r.stdout
    assert "| `O` |" in r.stdout  # agua listada
