import wx
import wx.dataview as dv
from ..core import iosgen

class IOSPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, label="Template:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.cmb = wx.ComboBox(self, style=wx.CB_READONLY, choices=[
            "Hostname",
            "Interface IP",
            "Static Route",
            "ACL (standard)",
            "ACL (extended)",
            "NAT Overload (PAT)",
            "NAT Static",
            "OSPF (single process)",
            "VLAN",
            "Switchport Access",
            "Switchport Trunk",
            "Port-Security (access)",
            "DHCP Pool",
            "Banner login"
        ])
        self.cmb.SetSelection(0)
        row.Add(self.cmb, 0, wx.RIGHT, 12)
        self.btn_gen = wx.Button(self, label="Generate")
        row.Add(self.btn_gen, 0)
        root.Add(row, 0, wx.ALL, 12)

        form_holder = wx.ScrolledWindow(self, style=wx.VSCROLL)
        form_holder.SetScrollRate(10,10)
        grid = wx.FlexGridSizer(0, 2, 6, 8)
        grid.AddGrowableCol(1, 1)
        self.kv = {}
        def add(label, key, val=""):
            grid.Add(wx.StaticText(form_holder, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
            ctrl = wx.TextCtrl(form_holder, value=val)
            grid.Add(ctrl, 1, wx.EXPAND)
            self.kv[key] = ctrl
        # Common fields prepared; not all are used by every template
        add("Interface", "ifname")
        add("IP", "ip")
        add("Mask", "mask")
        add("Hostname", "hostname")
        add("Destination", "dst")
        add("Next-hop", "nexthop")
        add("ACL number", "aclnum")
        add("Action (permit|deny)", "action", "permit")
        add("Protocol (tcp|udp|ip)", "proto", "tcp")
        add("Src", "src", "any")
        add("Src wildcard", "srcwc", "0.0.0.0")
        add("Dst", "dstnet", "any")
        add("Dst wildcard", "dstwc", "0.0.0.0")
        add("Dst port/eq", "dport", "80")
        add("Outside IF", "outside", "GigabitEthernet0/0")
        add("Inside subnet", "inside", "192.168.1.0 0.0.0.255")
        add("OSPF process", "ospfpid", "1")
        add("OSPF networks (net wc area; one per line)", "ospfnet", "10.0.0.0 0.0.0.255 0")
        add("VLAN ID", "vlanid", "10")
        add("VLAN Name", "vlanname", "USERS")
        add("Allowed VLANs (e.g., 10,20 or all)", "allowed", "all")
        add("Max MAC", "maxmac", "1")
        add("Violation (protect/restrict/shutdown)", "violation", "restrict")
        add("DHCP pool name", "poolname", "LAN_POOL")
        add("Default gateway", "defgw", "192.168.1.1")
        add("DNS server", "dns", "8.8.8.8")
        add("Excluded ranges (start-end; one per line)", "excluded", "192.168.1.2-192.168.1.50")
        add("Banner text", "banner", "Authorised access only")
        form_holder.SetSizer(grid)
        root.Add(form_holder, 1, wx.ALL | wx.EXPAND, 12)

        self.out = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        fnt = self.out.GetFont(); fnt.SetFaceName('Consolas' if 'Consolas' in wx.FontEnumerator().GetFacenames() else fnt.GetFaceName()); self.out.SetFont(fnt)
        self.out.SetMinSize((-1, 180))
        root.Add(self.out, 1, wx.ALL | wx.EXPAND, 12)

        foot = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_copy = wx.Button(self, label="Copy to Clipboard")
        foot.Add(self.btn_copy, 0)
        root.Add(foot, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.SetSizer(root)

        self.btn_gen.Bind(wx.EVT_BUTTON, self.on_generate)
        self.btn_copy.Bind(wx.EVT_BUTTON, self.on_copy)

    def on_copy(self, evt):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self.out.GetValue()))
            wx.TheClipboard.Close()

    def on_generate(self, evt):
        t = self.cmb.GetValue()
        g = self.kv  # shorthand
        try:
            if t == "Hostname":
                txt = iosgen.hostname(g["hostname"].GetValue().strip())
            elif t == "Interface IP":
                txt = iosgen.interface_ip(g["ifname"].GetValue().strip(), g["ip"].GetValue().strip(), g["mask"].GetValue().strip())
            elif t == "Static Route":
                txt = iosgen.static_route(g["dst"].GetValue().strip(), g["mask"].GetValue().strip(), g["nexthop"].GetValue().strip())
            elif t == "ACL (standard)":
                txt = iosgen.acl_standard(int(g["aclnum"].GetValue() or "1"), g["action"].GetValue().strip(), g["src"].GetValue().strip(), g["srcwc"].GetValue().strip())
            elif t == "ACL (extended)":
                txt = iosgen.acl_extended(int(g["aclnum"].GetValue() or "101"), g["action"].GetValue().strip(), g["proto"].GetValue().strip(),
                                          g["src"].GetValue().strip(), g["srcwc"].GetValue().strip(),
                                          g["dstnet"].GetValue().strip(), g["dstwc"].GetValue().strip(),
                                          g["dport"].GetValue().strip())
            elif t == "NAT Overload (PAT)":
                txt = iosgen.nat_overload(g["inside"].GetValue().strip(), g["outside"].GetValue().strip(), int(g["aclnum"].GetValue() or "1"))
            elif t == "NAT Static":
                txt = iosgen.nat_static(g["ip"].GetValue().strip(), g["dst"].GetValue().strip())
            elif t == "OSPF (single process)":
                nets = []
                for line in g["ospfnet"].GetValue().splitlines():
                    parts = [p for p in line.strip().split() if p]
                    if len(parts) >= 3:
                        nets.append((parts[0], parts[1], parts[2]))
                txt = iosgen.ospf_single_process(int(g["ospfpid"].GetValue() or "1"), nets)
            elif t == "VLAN":
                txt = iosgen.vlan(int(g["vlanid"].GetValue() or "10"), (g["vlanname"].GetValue().strip() or None))
            elif t == "Switchport Access":
                txt = iosgen.switchport_access(g["ifname"].GetValue().strip(), int(g["vlanid"].GetValue() or "10"))
            elif t == "Switchport Trunk":
                txt = iosgen.switchport_trunk(g["ifname"].GetValue().strip(), g["allowed"].GetValue().strip())
            elif t == "Port-Security (access)":
                txt = iosgen.port_security_access(g["ifname"].GetValue().strip(), int(g["maxmac"].GetValue() or "1"), True, g["violation"].GetValue().strip())
            elif t == "DHCP Pool":
                excluded = []
                for line in g["excluded"].GetValue().splitlines():
                    if "-" in line:
                        start,end = [p.strip() for p in line.split("-",1)]
                        excluded.append((start,end))
                txt = iosgen.dhcp_pool(g["poolname"].GetValue().strip(), g["ip"].GetValue().strip(), g["mask"].GetValue().strip(), g["defgw"].GetValue().strip(), g["dns"].GetValue().strip(), excluded)
            elif t == "Banner login":
                txt = iosgen.banner_login(g["banner"].GetValue())
            else:
                txt = "! Unsupported template"
        except Exception as e:
            txt = f"! Error: {e}"
        self.out.SetValue(txt)
