from typer.testing import CliRunner

from qchem_leak_screen.cli import app

runner = CliRunner()


def test_cli_inline_smiles_pass():
    r = runner.invoke(
        app,
        [
            "check",
            "--smiles",
            "O",
            "--props",
            '{"homo_ev":-12.6,"lumo_ev":-1.2,"gap_ev":11.4,"dipole_debye":1.85}',
            "--format",
            "json",
        ],
    )
    assert r.exit_code == 0, r.output
    assert '"verdict": "PASS"' in r.output


def test_cli_inline_hallucinated_fail():
    r = runner.invoke(
        app,
        [
            "check",
            "--smiles",
            "c1ccccc1",
            "--props",
            '{"homo_ev":-3.0,"lumo_ev":-1.0,"gap_ev":-2.0,"dipole_debye":999.0}',
            "--format",
            "json",
        ],
    )
    assert r.exit_code == 1, r.output
    assert '"verdict": "FAIL"' in r.output


def test_cli_bad_input_exit2():
    r = runner.invoke(app, ["check", "--smiles", "O", "--props", "not-json"])
    assert r.exit_code == 2
