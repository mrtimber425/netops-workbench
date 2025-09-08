import wx
import wx.dataview as dv
import time
from collections import Counter, defaultdict
from ..utils.auto_dv import AutoSizeDVColsMixin

HAVE_SCAPY = False
try:
    from scapy.all import rdpcap, TCP, UDP, IP  # type: ignore
    HAVE_SCAPY = True
except Exception:
    pass

class PacketPanel(wx.Panel, AutoSizeDVColsMixin):
    def __init__(self, parent):
        super().__init__(parent)
        self._packets = []
        self._rows = []
        self._build()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        bar = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_open = wx.Button(self, label="Open PCAP/PCAPNG")
        self.txt_filter = wx.TextCtrl(self, value="", style=wx.TE_PROCESS_ENTER)
        self.btn_apply = wx.Button(self, label="Filter")
        self.spin_limit = wx.SpinCtrl(self, min=100, max=200000, initial=20000)
        bar.Add(self.btn_open, 0, wx.RIGHT, 8)
        bar.Add(wx.StaticText(self, label="Filter (proto/ip/port/text):"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        bar.Add(self.txt_filter, 1, wx.RIGHT, 8)
        bar.Add(self.btn_apply, 0, wx.RIGHT, 8)
        bar.Add(wx.StaticText(self, label="Max packets:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        bar.Add(self.spin_limit, 0)
        root.Add(bar, 0, wx.ALL | wx.EXPAND, 12)

        split = wx.BoxSizer(wx.HORIZONTAL)

        self.dv = dv.DataViewListCtrl(self, style=dv.DV_ROW_LINES | dv.DV_VERT_RULES)
        for col in ["Time", "Src", "Sport", "Dst", "Dport", "Proto", "Len", "Info"]:
            self.dv.AppendTextColumn(col, width=120 if col not in ("Info","Time") else 200)
        split.Add(self.dv, 1, wx.ALL | wx.EXPAND, 8)
        self._bind_autosize(self.dv)

        self.stats = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        split.Add(self.stats, 1, wx.ALL | wx.EXPAND, 8)

        root.Add(split, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)
        self.SetSizer(root)

        self.btn_open.Bind(wx.EVT_BUTTON, self.on_open)
        self.btn_apply.Bind(wx.EVT_BUTTON, self.on_filter)
        self.txt_filter.Bind(wx.EVT_TEXT_ENTER, self.on_filter)

        if not HAVE_SCAPY:
            self.stats.SetValue("Install scapy to parse PCAPs: pip install scapy")

    def on_open(self, evt):
        with wx.FileDialog(self, "Open PCAP/PCAPNG", wildcard="PCAP files (*.pcap;*.pcapng)|*.pcap;*.pcapng|All files (*.*)|*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            path = dlg.GetPath()
        if not HAVE_SCAPY:
            wx.MessageBox("Scapy is required: pip install scapy", "Missing dependency", wx.OK | wx.ICON_WARNING)
            return
        self.load_pcap(path)

    def load_pcap(self, path):
        limit = int(self.spin_limit.GetValue())
        try:
            pkts = rdpcap(path)[:limit]
        except Exception as e:
            wx.MessageBox(f"Failed to read pcap: {e}", "Error", wx.OK | wx.ICON_ERROR)
            return
        self._packets = pkts
        self.apply_rows(pkts)
        self.txt_filter.SetValue("")
        self.update_stats(pkts, note=f"Loaded {len(pkts)} packets from {path}")

    def apply_rows(self, pkts):
        self.dv.DeleteAllItems()
        self._rows.clear()
        for p in pkts:
            t = time.strftime("%H:%M:%S", time.localtime(getattr(p, 'time', time.time())))
            proto = p.lastlayer().__class__.__name__
            length = len(p)
            src = getattr(getattr(p, 'src', None) or getattr(getattr(p, 'payload', None), 'src', None), 'upper', lambda: None)()
            dst = getattr(getattr(p, 'dst', None) or getattr(getattr(p, 'payload', None), 'dst', None), 'upper', lambda: None)()
            sport = getattr(getattr(p, 'sport', None) or getattr(getattr(p, 'payload', None), 'sport', None), 'real', lambda: None)()
            dport = getattr(getattr(p, 'dport', None) or getattr(getattr(p, 'payload', None), 'dport', None), 'real', lambda: None)()
            info = p.summary()
            row = [t, src or "", str(sport or ""), dst or "", str(dport or ""), proto, str(length), info]
            self.dv.AppendItem(row)
            self._rows.append((row, p))

    def parse_filter(self, text):
        terms = [t.strip() for t in text.split() if t.strip()]
        keys = {"proto": None, "ip": None, "port": None, "text": None}
        for t in terms:
            if t.lower() in ("tcp","udp","icmp","dns","http","tls"):
                keys["proto"] = t.upper()
            elif t.isdigit():
                keys["port"] = int(t)
            elif "/" in t or ":" in t or t.count(".") == 3:
                keys["ip"] = t
            else:
                keys["text"] = t
        return keys

    def on_filter(self, evt):
        if not self._packets:
            return
        f = self.parse_filter(self.txt_filter.GetValue().strip())
        if not any(f.values()):
            self.apply_rows(self._packets)
            self.update_stats(self._packets, note="Filter cleared")
            return
        filtered = []
        for p in self._packets:
            ok = True
            if f["proto"]:
                if f["proto"] not in p.summary().upper():
                    ok = False
            if ok and f["ip"]:
                if f["ip"] not in p.summary():
                    ok = False
            if ok and f["port"]:
                if (hasattr(p, 'sport') and p.sport == f["port"]) or (hasattr(p, 'dport') and p.dport == f["port"]):
                    pass
                else:
                    ok = False
            if ok and f["text"]:
                if f["text"].lower() not in p.summary().lower():
                    ok = False
            if ok:
                filtered.append(p)
        self.apply_rows(filtered)
        self.update_stats(filtered, note=f"Filter: {self.txt_filter.GetValue()}")

    def update_stats(self, pkts, note=""):
        proto = Counter(p.lastlayer().__class__.__name__ for p in pkts)
        talk_src = Counter(getattr(p, 'src', getattr(getattr(p,'payload',None),'src', None)) for p in pkts)
        talk_dst = Counter(getattr(p, 'dst', getattr(getattr(p,'payload',None),'dst', None)) for p in pkts)
        lines = [note, "", "Protocols:"]
        for k,v in proto.most_common():
            lines.append(f" - {k}: {v}")
        lines.append("")
        lines.append("Top talkers (src):")
        for k,v in talk_src.most_common(10):
            lines.append(f" - {k}: {v}")
        lines.append("Top talkers (dst):")
        for k,v in talk_dst.most_common(10):
            lines.append(f" - {k}: {v}")
        self.stats.SetValue("\\n".join(lines))
