from ipaddress import ip_network, ip_address, IPv4Network

def hosts_to_prefix(hosts: int) -> int:
    # required addresses include network+broadcast (except /31)
    needed = hosts + 2 if hosts > 0 else 0
    prefix = 32
    size = 1
    while size < needed and prefix > 0:
        size <<= 1
        prefix -= 1
    # cap at /30 to keep >0 usable; /31 reserved for ptp (not auto here)
    if prefix > 30:
        prefix = 30
    return prefix

def split_until(block: IPv4Network, want_prefix: int) -> tuple[IPv4Network, list[IPv4Network]]:
    """Split 'block' until we obtain one subnet at want_prefix. Return (allocated, leftovers)."""
    leftovers = []
    curr = block
    while curr.prefixlen < want_prefix:
        left, right = list(curr.subnets(prefixlen_diff=1))
        # allocate from left; keep right as free; but we also continue splitting the left
        leftovers.append(right)
        curr = left
    return curr, leftovers

def carve(free_list: list[IPv4Network], want_prefix: int) -> tuple[IPv4Network | None, list[IPv4Network]]:
    """Take first block that can fit want_prefix; return (allocated, new_free_list)."""
    new_free = free_list.copy()
    for i, blk in enumerate(free_list):
        if blk.prefixlen > want_prefix:
            # too small, continue
            continue
        # blk is bigger or equal
        alloc, remainers = split_until(blk, want_prefix)
        # replace original with remainers (and keep any unused part before/after)
        new_free.pop(i)
        # Remaining space inside 'blk' is the collected 'remainers'
        new_free[i:i] = remainers  # insert at same position
        return alloc, new_free
    return None, free_list

def allocate_vlsm(base_cidr: str, demands: list[dict]) -> dict:
    """
    demands: list of {"name": str, "hosts": int}
    Greedy largest-first allocation with a proper free-list to reduce fragmentation.
    """
    base: IPv4Network = ip_network(base_cidr, strict=True)
    reqs = sorted(demands, key=lambda d: d["hosts"], reverse=True)

    free = [base]
    placed: list[tuple[dict, IPv4Network]] = []

    for d in reqs:
        want = hosts_to_prefix(d["hosts"])
        alloc, free = carve(free, want)
        if alloc is None:
            return {"ok": False, "error": f"No space for {d['name']} (/{want})", "blocks": [], "gaps": []}
        placed.append((d, alloc))

    # Remaining free list are gaps
    gaps = [str(n) for n in sorted(free, key=lambda n: int(ip_address(str(n.network_address))))]

    blocks = []
    for d, net in sorted(placed, key=lambda x: int(ip_address(str(x[1].network_address)))):
        total = net.num_addresses
        usable = max(total - 2, 0) if net.prefixlen < 31 else (2 if net.prefixlen == 31 else 1)
        gw = f"{list(net.hosts())[0]}" if usable > 0 else str(net.network_address)
        blocks.append({
            "name": d["name"],
            "cidr": f"{net.network_address}/{net.prefixlen}",
            "usable_hosts": usable,
            "gateway": gw,
        })

    return {"ok": True, "error": None, "blocks": blocks, "gaps": gaps}
