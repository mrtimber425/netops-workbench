import wx
import wx.grid as gridlib
from ..core.firewall import Rule, Engine, Packet
from ..utils.tablestyle import style_grid
from ..utils import validators

class FirewallPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.engine = Engine()
        self._build()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        self.grid = gridlib.Grid(self)
        self.grid.CreateGrid(6, 6)
        style_grid(self.grid, row_h=30, def_col_w=150, header_h=26, rowlabel_w=30)
        self.grid.SetColSize(0, 160)
        self.grid.SetColSize(1, 160)
        self.grid.SetColSize(2, 160)
        self.grid.SetColSize(3, 120)
        self.grid.SetColSize(4, 100)
        self.grid.SetColSize(5, 200)
        self.grid.SetColLabelValue(0, "Action (allow/deny)")
        self.grid.SetColLabelValue(1, "Src CIDR")
        self.grid.SetColLabelValue(2, "Dst CIDR")
        self.grid.SetColLabelValue(3, "Proto (tcp/udp/any)")
        self.grid.SetColLabelValue(4, "Port (int/any)")
        self.grid.SetColLabelValue(5, "Comment")
        root.Add(self.grid, 1, wx.ALL | wx.EXPAND, 12)

        row = wx.BoxSizer(wx.HORIZONTAL)
        self.txt_src = wx.TextCtrl(self, value="10.0.0.10")
        self.txt_dst = wx.TextCtrl(self, value="10.0.1.20")
        self.txt_proto = wx.TextCtrl(self, value="tcp")
        self.txt_port = wx.TextCtrl(self, value="22")
        btn_test = wx.Button(self, label="Test Packet")
        btn_test.Bind(wx.EVT_BUTTON, self.on_test)
        row.Add(wx.StaticText(self, label="Test src:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row.Add(self.txt_src, 0, wx.RIGHT, 8)
        row.Add(wx.StaticText(self, label="dst:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row.Add(self.txt_dst, 0, wx.RIGHT, 8)
        row.Add(wx.StaticText(self, label="proto:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row.Add(self.txt_proto, 0, wx.RIGHT, 8)
        row.Add(wx.StaticText(self, label="port:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        row.Add(self.txt_port, 0, wx.RIGHT, 8)
        row.Add(btn_test, 0)
        root.Add(row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.out = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        root.Add(self.out, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)

        row2 = wx.BoxSizer(wx.HORIZONTAL)
        btn_apply = wx.Button(self, label="Apply Rules")
        btn_reset = wx.Button(self, label="Reset Rules")
        btn_apply.Bind(wx.EVT_BUTTON, self.on_apply)
        btn_reset.Bind(wx.EVT_BUTTON, self.on_reset)
        row2.Add(btn_apply, 0, wx.RIGHT, 8)
        row2.Add(btn_reset, 0)
        root.Add(row2, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.SetSizer(root)

    def on_apply(self, evt):
        rules = []
        for r in range(self.grid.GetNumberRows()):
            action = self.grid.GetCellValue(r, 0).strip().lower()
            src = self.grid.GetCellValue(r, 1).strip()
            dst = self.grid.GetCellValue(r, 2).strip()
            proto = self.grid.GetCellValue(r, 3).strip().lower() or "any"
            port = self.grid.GetCellValue(r, 4).strip().lower() or "any"
            if not action:
                continue
            if action not in ("allow", "deny"):
                continue
            if not src or not dst:
                continue
            try:
                port_val = None if port == "any" else int(port)
            except Exception:
                continue
            try:
                rules.append(Rule(action=action, src=src, dst=dst, proto=proto, port=port_val, comment=self.grid.GetCellValue(r, 5)))
            except Exception:
                continue
        self.engine.set_rules(rules)
        self.out.SetValue(f"Applied {len(rules)} rules.")

    def on_reset(self, evt):
        self.engine.set_rules([])
        self.out.SetValue("Rules cleared.")

    def on_test(self, evt):
        src = self.txt_src.GetValue().strip()
        dst = self.txt_dst.GetValue().strip()
        proto = self.txt_proto.GetValue().strip().lower() or "any"
        port_txt = self.txt_port.GetValue().strip().lower() or "any"
        try:
            p = None if port_txt == "any" else int(port_txt)
        except Exception:
            self.out.SetValue("Invalid port.")
            return
        pkt = Packet(src=src, dst=dst, proto=proto, port=p)
        verdict, matched = self.engine.evaluate(pkt)
        lines = [f"Verdict: {verdict}"]
        if matched is not None:
            lines.append(f"Matched rule index: {matched}")
        else:
            lines.append("Matched rule: <implicit deny>")
        self.out.SetValue("\n".join(lines))
