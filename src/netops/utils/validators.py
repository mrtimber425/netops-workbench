from ipaddress import ip_interface, ip_network

def is_cidr(text: str) -> bool:
    try:
        ip_interface(text)
        return True
    except Exception:
        return False

def is_network_cidr(text: str) -> bool:
    try:
        n = ip_network(text, strict=True)
        return True
    except Exception:
        return False
