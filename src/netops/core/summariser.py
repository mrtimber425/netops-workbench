from ipaddress import ip_network, collapse_addresses

def summarise(cidrs: list[str]) -> list[str]:
    nets = [ip_network(c, strict=False) for c in cidrs]
    collapsed = collapse_addresses(nets)
    return [str(n) for n in collapsed]
