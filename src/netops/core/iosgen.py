from typing import List

def hostname(name: str) -> str:
    return f"hostname {name}"

def interface_ip(ifname: str, ip: str, mask: str, no_shutdown: bool=True) -> str:
    lines = [f"interface {ifname}", f" ip address {ip} {mask}"]
    if no_shutdown:
        lines.append(" no shutdown")
    return "\n".join(lines)

def static_route(dst: str, mask: str, next_hop: str, distance: int|None=None) -> str:
    cmd = f"ip route {dst} {mask} {next_hop}"
    if distance is not None:
        cmd += f" {distance}"
    return cmd

def acl_standard(number: int, action: str, src: str, wildcard: str="0.0.0.0") -> str:
    return f"access-list {number} {action} {src} {wildcard}"

def acl_extended(number: int, action: str, proto: str, src: str, src_wc: str, dst: str, dst_wc: str, dport: str|None=None) -> str:
    parts = [f"access-list {number} {action} {proto} {src} {src_wc} {dst} {dst_wc}"]
    if dport:
        parts += ["eq", dport]
    return " ".join(parts)

def nat_overload(inside: str, outside_if: str, acl_num: int) -> str:
    # Example assumes ACL defines inside local addresses
    return "\n".join([
        f"ip access-list standard {acl_num}",
        f" permit {inside}",
        "ip nat inside source list {0} interface {1} overload".format(acl_num, outside_if)
    ])

def nat_static(local_ip: str, global_ip: str) -> str:
    return f"ip nat inside source static {local_ip} {global_ip}"

def ospf_single_process(process_id: int, networks: List[tuple]) -> str:
    """
    networks: list of tuples (network, wildcard, area)
    """
    lines = [f"router ospf {process_id}"]
    for net, wc, area in networks:
        lines.append(f" network {net} {wc} area {area}")
    return "\n".join(lines)

def vlan(vlan_id: int, name: str|None=None) -> str:
    lines = [f"vlan {vlan_id}"]
    if name:
        lines.append(f" name {name}")
    return "\n".join(lines)

def switchport_access(ifname: str, vlan_id: int) -> str:
    return "\n".join([
        f"interface {ifname}",
        " switchport mode access",
        f" switchport access vlan {vlan_id}",
        " spanning-tree portfast"
    ])

def switchport_trunk(ifname: str, allowed: str="all") -> str:
    lines = [f"interface {ifname}", " switchport mode trunk"]
    if allowed != "all":
        lines.append(f" switchport trunk allowed vlan {allowed}")
    return "\n".join(lines)

def port_security_access(ifname: str, max_mac: int=1, sticky: bool=True, violation: str="restrict") -> str:
    lines = [f"interface {ifname}", " switchport mode access", " switchport port-security", f" switchport port-security maximum {max_mac}"]
    if sticky:
        lines.append(" switchport port-security mac-address sticky")
    lines.append(f" switchport port-security violation {violation}")
    return "\n".join(lines)

def dhcp_pool(name: str, network: str, mask: str, default_router: str, dns: str|None=None, excluded: List[tuple]=[]) -> str:
    lines = []
    for start, end in excluded:
        lines.append(f"ip dhcp excluded-address {start} {end}")
    lines += [f"ip dhcp pool {name}",
              f" network {network} {mask}",
              f" default-router {default_router}"]
    if dns:
        lines.append(f" dns-server {dns}")
    return "\n".join(lines)

def banner_login(text: str) -> str:
    delim = "#"
    return f"banner login {delim}{text}{delim}"
