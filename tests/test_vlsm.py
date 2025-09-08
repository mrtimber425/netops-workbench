from netops.core.vlsm import allocate_vlsm

def test_vlsm():
    base = "10.20.0.0/20"
    demands = [{"name": "A", "hosts": 200}, {"name": "B", "hosts": 120}, {"name": "C", "hosts": 60}]
    plan = allocate_vlsm(base, demands)
    assert plan["ok"] is True
    assert len(plan["blocks"]) == 3
