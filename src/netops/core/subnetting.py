from ipaddress import ip_interface, ip_network

def describe_cidr(cidr: str) -> dict:
    iface = ip_interface(cidr)
    net = iface.network
    is_31 = net.prefixlen == 31
    is_32 = net.prefixlen == 32

    netmask = str(net.netmask)
    wildcard = str(net.hostmask)  # wildcard/hostmask
    broadcast = None if is_32 else str(net.broadcast_address)
    usable_hosts = 0
    first_usable = last_usable = None
    if is_32:
        usable_hosts = 1
        first_usable = last_usable = str(net.network_address)
    elif is_31:
        usable_hosts = 2  # point-to-point
        addrs = list(net.hosts())
        first_usable = str(addrs[0])
        last_usable = str(addrs[1])
    else:
        hosts = list(net.hosts())
        usable_hosts = len(hosts)
        first_usable = str(hosts[0]) if hosts else None
        last_usable = str(hosts[-1]) if hosts else None

    return {
        "network": str(net.network_address) + f"/{net.prefixlen}",
        "netmask": netmask,
        "wildcard": wildcard,
        "broadcast": broadcast,
        "usable_hosts": usable_hosts,
        "first_usable": first_usable,
        "last_usable": last_usable,
        "is_31": is_31,
        "is_32": is_32,
    }
