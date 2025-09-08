import shutil, subprocess, xml.etree.ElementTree as ET

def has_nmap() -> bool:
    return shutil.which("nmap") is not None

def run_nmap_xml(
    targets: list[str],
    scan_type: str = "syn",       # "syn", "connect", "udp"
    service_version: bool = True, # -sV
    os_detect: bool = False,      # -O
    no_ping: bool = False,        # -Pn
    top_ports: int | None = 200,
    ports: str | None = None,     # e.g., "22,80,443" or "1-1024"
    timing: str = "T3",           # T0..T5
):
    """
    Build an nmap command and parse XML output.
    """
    if not has_nmap():
        return {"ok": False, "error": "nmap not found in PATH.", "hosts": []}

    args = ["nmap", "-oX", "-"]  # XML to stdout

    # scan type
    if scan_type == "syn":
        args.append("-sS")
    elif scan_type == "connect":
        args.append("-sT")
    elif scan_type == "udp":
        args.append("-sU")

    if service_version:
        args.append("-sV")
    if os_detect:
        args.append("-O")
    if no_ping:
        args.append("-Pn")

    # timing
    if timing.upper() in ("T0","T1","T2","T3","T4","T5"):
        args.append("-" + timing.upper())

    # ports
    if ports:
        args += ["-p", ports]
    elif top_ports:
        args += ["--top-ports", str(top_ports)]

    args += targets

    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=1200)
        if proc.returncode != 0:
            return {"ok": False, "error": proc.stderr.strip() or "nmap error", "hosts": []}
        return {"ok": True, "error": None, "hosts": parse_nmap_xml(proc.stdout), "cmd": " ".join(args)}
    except Exception as e:
        return {"ok": False, "error": str(e), "hosts": [], "cmd": " ".join(args)}

def parse_nmap_xml(xml_text: str):
    hosts = []
    tree = ET.fromstring(xml_text)
    for h in tree.findall("host"):
        status = h.find("status").attrib.get("state", "unknown") if h.find("status") is not None else "unknown"
        addr = None
        mac = None
        for a in h.findall("address"):
            if a.attrib.get("addrtype") == "ipv4":
                addr = a.attrib.get("addr")
            if a.attrib.get("addrtype") == "mac":
                mac = a.attrib.get("addr")
        hostname = None
        hn = h.find("hostnames")
        if hn is not None:
            n = hn.find("hostname")
            if n is not None:
                hostname = n.attrib.get("name")
        osmatch = None
        osnode = h.find("os")
        if osnode is not None:
            om = osnode.find("osmatch")
            if om is not None:
                osmatch = om.attrib.get("name")
        services = []
        ports = h.find("ports")
        if ports is not None:
            for p in ports.findall("port"):
                portid = p.attrib.get("portid")
                proto = p.attrib.get("protocol")
                state = p.find("state").attrib.get("state") if p.find("state") is not None else "unknown"
                service = p.find("service")
                product = service.attrib.get("product") if service is not None else None
                version = service.attrib.get("version") if service is not None else None
                name = service.attrib.get("name") if service is not None else None
                services.append({
                    "port": int(portid) if portid and portid.isdigit() else None,
                    "proto": proto,
                    "state": state,
                    "name": name,
                    "product": product,
                    "version": version
                })
        hosts.append({
            "ip": addr,
            "mac": mac,
            "hostname": hostname,
            "status": status,
            "os": osmatch,
            "services": services
        })
    return hosts
