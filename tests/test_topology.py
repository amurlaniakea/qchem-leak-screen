from qchem_leak_screen.core.dataclasses import MolInput, PropPrediction
from qchem_leak_screen.core.topology import check_topology


def _mol(smiles, **kw):
    return MolInput(smiles=smiles, predicted=PropPrediction(**kw))


def test_r1_benzene_neutral_ok():
    v = check_topology(_mol("c1ccccc1"))
    assert v is None, v


def test_r1_unbalanced_smiles_fail():
    v = check_topology(_mol("c1ccccc"))
    assert v is not None and v.rule_id == "R1" and v.severity == "FAIL"
    assert "unparseable" in v.reason


def test_r1_extreme_charge_fail():
    # benceno con carga +5 declarada => hallucinacion estructural
    v = check_topology(_mol("c1ccccc1[CH+5]"))
    assert v is not None and v.rule_id == "R1"
    assert "net_charge_out_of_range" in v.reason, v.reason
