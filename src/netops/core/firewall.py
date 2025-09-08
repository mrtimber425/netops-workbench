from dataclasses import dataclass
from ipaddress import ip_network, ip_address

@dataclass
class Rule:
    action: str  # "allow" or "deny"
    src: str     # CIDR
    dst: str     # CIDR
    proto: str   # "tcp" | "udp" | "any"
    port: int | None  # None -> any
    comment: str = ""

@dataclass
class Packet:
    src: str
    dst: str
    proto: str
    port: int | None

class Engine:
    def __init__(self):
        self.rules: list[Rule] = []

    def set_rules(self, rules: list[Rule]):
        self.rules = rules

    def evaluate(self, pkt: Packet) -> tuple[str, int | None]:
        """Return (verdict, matched_rule_index). Default implicit deny."""
        ps = ip_address(pkt.src)
        pd = ip_address(pkt.dst)
        for idx, r in enumerate(self.rules):
            ns = ip_network(r.src, strict=False)
            nd = ip_network(r.dst, strict=False)
            if ps in ns and pd in nd:
                # proto
                if r.proto != "any" and pkt.proto != r.proto:
                    continue
                # port
                if r.port is not None and pkt.port != r.port:
                    continue
                return r.action, idx
        return "deny", None
