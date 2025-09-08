import platform
import subprocess
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

def _ping_once(host: str, timeout: float = 1.0) -> dict:
    system = platform.system().lower()
    if system == "windows":
        # -n 1 -> one echo, -w timeout(ms)
        cmd = ["ping", "-n", "1", "-w", str(int(timeout*1000)), host]
    else:
        # -c 1 -> one echo, -W timeout(s)
        cmd = ["ping", "-c", "1", "-W", str(int(timeout)), host]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+1)
        ok = out.returncode == 0
        rtt_ms = None
        if ok:
            m = re.search(r"time[=<]([\d\.]+)\s*ms", out.stdout)
            if m:
                rtt_ms = float(m.group(1))
        return {"host": host, "up": ok, "rtt_ms": rtt_ms}
    except Exception:
        return {"host": host, "up": False, "rtt_ms": None}

def expand_targets(targets: list[str]) -> list[str]:
    ips = []
    for t in targets:
        t = t.strip()
        if not t:
            continue
        if "/" in t:
            net = ipaddress.ip_network(t, strict=False)
            for ip in net.hosts():
                ips.append(str(ip))
        else:
            ips.append(t)
    return ips

def ping_sweep(targets: list[str], timeout: float = 1.0, max_workers: int = 64):
    ips = expand_targets(targets)
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(_ping_once, ip, timeout) for ip in ips]
        for f in as_completed(futs):
            results.append(f.result())
    # Sort by IP
    def ip_key(r):
        try:
            return int(ipaddress.ip_address(r["host"]))
        except Exception:
            return 0
    results.sort(key=ip_key)
    return results
