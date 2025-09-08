from ipaddress import ip_network
try:
    from scapy.all import ARP, Ether, srp, conf  # type: ignore
    HAVE_SCAPY = True
except Exception:
    HAVE_SCAPY = False

def arp_scan(cidr: str, timeout: float = 2.0) -> dict:
    """
    Returns {"ok": bool, "error": str|None, "hosts": [{"ip": "...", "mac": "..."}]}
    """
    if not HAVE_SCAPY:
        return {"ok": False, "error": "Scapy not installed. pip install scapy; requires Npcap on Windows.", "hosts": []}
    try:
        # Validate
        ip_network(cidr, strict=False)
        conf.verb = 0
        pkt = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=cidr)  # type: ignore
        ans, _ = srp(pkt, timeout=timeout)  # type: ignore
        hosts = []
        for snd, rcv in ans:
            hosts.append({"ip": rcv.psrc, "mac": rcv.hwsrc})
        return {"ok": True, "error": None, "hosts": hosts}
    except Exception as e:
        return {"ok": False, "error": str(e), "hosts": []}
