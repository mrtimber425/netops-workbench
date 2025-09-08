from netops.core.subnetting import describe_cidr

def test_basic():
    info = describe_cidr("10.0.0.1/22")
    assert info["netmask"] == "255.255.252.0"
    assert info["broadcast"] == "10.0.3.255"
    assert info["usable_hosts"] == 1022
