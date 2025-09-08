import wx
import socket

try:
    import dns.resolver  # type: ignore
    HAVE_DNSPYTHON = True
except Exception:
    HAVE_DNSPYTHON = False

class DNSPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(self, label="Host/Domain:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.txt_host = wx.TextCtrl(self, value="example.com", size=(260,-1))
        row.Add(self.txt_host, 0, wx.RIGHT, 8)
        btn_a = wx.Button(self, label="A/AAAA")
        btn_mx = wx.Button(self, label="MX (needs dnspython)")
        btn_ns = wx.Button(self, label="NS (needs dnspython)")
        btn_txt = wx.Button(self, label="TXT (needs dnspython)")
        btn_a.Bind(wx.EVT_BUTTON, self.on_a)
        btn_mx.Bind(wx.EVT_BUTTON, self.on_mx)
        btn_ns.Bind(wx.EVT_BUTTON, self.on_ns)
        btn_txt.Bind(wx.EVT_BUTTON, self.on_txt)
        row.Add(btn_a, 0, wx.RIGHT, 8)
        row.Add(btn_mx, 0, wx.RIGHT, 8)
        row.Add(btn_ns, 0, wx.RIGHT, 8)
        row.Add(btn_txt, 0)
        sizer.Add(row, 0, wx.ALL, 12)

        self.out = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        sizer.Add(self.out, 1, wx.ALL | wx.EXPAND, 12)
        self.SetSizer(sizer)

    def on_a(self, evt):
        host = self.txt_host.GetValue().strip()
        lines = [f"Host: {host}"]
        try:
            a = socket.gethostbyname_ex(host)
            lines.append("A Records:")
            for ip in a[2]:
                lines.append(f" - {ip}")
        except Exception as e:
            lines.append(f"A lookup error: {e}")
        try:
            info = socket.getaddrinfo(host, None, socket.AF_INET6)
            v6s = sorted(set([t[4][0] for t in info]))
            if v6s:
                lines.append("AAAA Records:")
                for ip in v6s:
                    lines.append(f" - {ip}")
        except Exception as e:
            lines.append(f"AAAA lookup note: {e}")
        self.out.SetValue("\n".join(lines))

    def on_mx(self, evt):
        self._dns_query("MX")

    def on_ns(self, evt):
        self._dns_query("NS")

    def on_txt(self, evt):
        self._dns_query("TXT")

    def _dns_query(self, rtype: str):
        host = self.txt_host.GetValue().strip()
        if not HAVE_DNSPYTHON:
            self.out.SetValue(f"{rtype} requires dnspython. Install with: pip install dnspython")
            return
        lines = [f"{rtype} for {host}:"]
        try:
            answers = dns.resolver.resolve(host, rtype, lifetime=4.0) # type: ignore
            for r in answers:
                lines.append(f" - {r.to_text()}")
        except Exception as e:
            lines.append(f"Lookup error: {e}")
        self.out.SetValue("\n".join(lines))
