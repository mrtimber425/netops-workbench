import wx
import wx.grid as gridlib
from ..core import vlsm
from ..utils import validators
from ..utils.tablestyle import style_grid
from ipaddress import ip_network

class VLSMPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        # Top controls
        top = wx.BoxSizer(wx.HORIZONTAL)
        top.Add(wx.StaticText(self, label="Base CIDR:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.txt_base = wx.TextCtrl(self, value="10.20.0.0/20", size=(200,-1))
        top.Add(self.txt_base, 0, wx.RIGHT, 12)
        btn_add = wx.Button(self, label="Add Row")
        btn_del = wx.Button(self, label="Remove Selected")
        btn_calc = wx.Button(self, label="Allocate")
        btn_add.Bind(wx.EVT_BUTTON, self.on_add)
        btn_del.Bind(wx.EVT_BUTTON, self.on_del)
        btn_calc.Bind(wx.EVT_BUTTON, self.on_calc)
        top.Add(btn_add, 0, wx.RIGHT, 8)
        top.Add(btn_del, 0, wx.RIGHT, 8)
        top.Add(btn_calc, 0)
        root.Add(top, 0, wx.ALL, 12)

        # Demand grid (input)
        self.grid = gridlib.Grid(self)
        self.grid.CreateGrid(5, 2)
        style_grid(self.grid, row_h=32, def_col_w=160, header_h=28, rowlabel_w=30)
        self.grid.SetColLabelValue(0, "Subnet Name")
        self.grid.SetColLabelValue(1, "Required Hosts")
        self.grid.SetColSize(0, 220)
        self.grid.SetColSize(1, 140)
        for r in range(5):
            self.grid.SetCellValue(r, 0, f"net{r+1}")
            self.grid.SetCellValue(r, 1, "50")
        root.Add(self.grid, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)

        # Split summary/IPs
        split = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        p1 = wx.Panel(split); p2 = wx.Panel(split)
        split.SetMinimumPaneSize(120)

        # Allocation summary grid
        s1 = wx.BoxSizer(wx.VERTICAL)
        self.grid_alloc = gridlib.Grid(p1)
        self.grid_alloc.CreateGrid(0, 6)
        style_grid(self.grid_alloc, row_h=28, def_col_w=150, header_h=26, rowlabel_w=0)
        self.grid_alloc.SetColLabelValue(0, "Name")
        self.grid_alloc.SetColLabelValue(1, "CIDR")
        self.grid_alloc.SetColLabelValue(2, "Usable")
        self.grid_alloc.SetColLabelValue(3, "Gateway")
        self.grid_alloc.SetColLabelValue(4, "First Usable")
        self.grid_alloc.SetColLabelValue(5, "Last Usable")
        self.grid_alloc.SetColSize(0, 180)
        self.grid_alloc.SetColSize(1, 160)
        self.grid_alloc.SetColSize(2, 90)
        self.grid_alloc.SetColSize(3, 160)
        self.grid_alloc.SetColSize(4, 160)
        self.grid_alloc.SetColSize(5, 160)
        s1.Add(self.grid_alloc, 1, wx.ALL | wx.EXPAND, 8)
        p1.SetSizer(s1)

        # IPs grid + controls
        s2 = wx.BoxSizer(wx.VERTICAL)
        bar = wx.BoxSizer(wx.HORIZONTAL)
        bar.Add(wx.StaticText(p2, label="Max IPs to display:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.spin_max = wx.SpinCtrl(p2, min=1, max=200000, initial=4096)
        bar.Add(self.spin_max, 0, wx.RIGHT, 12)
        self.btn_export = wx.Button(p2, label="Export CSV (selected subnet)")
        bar.Add(self.btn_export, 0)
        s2.Add(bar, 0, wx.ALL, 8)

        self.grid_ips = gridlib.Grid(p2)
        self.grid_ips.CreateGrid(0, 2)
        style_grid(self.grid_ips, row_h=26, def_col_w=180, header_h=26, rowlabel_w=0)
        self.grid_ips.SetColLabelValue(0, "IP")
        self.grid_ips.SetColLabelValue(1, "Flags")
        self.grid_ips.SetColSize(0, 220)
        self.grid_ips.SetColSize(1, 120)
        s2.Add(self.grid_ips, 1, wx.ALL | wx.EXPAND, 8)
        p2.SetSizer(s2)

        split.SplitHorizontally(p1, p2, sashPosition=200)
        root.Add(split, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)

        # Output (text)
        self.out = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        fnt = self.out.GetFont(); fnt.SetFaceName('Consolas' if 'Consolas' in wx.FontEnumerator().GetFacenames() else fnt.GetFaceName()); self.out.SetFont(fnt)
        root.Add(self.out, 0, wx.ALL | wx.EXPAND, 12)

        self.SetSizer(root)

        # Events
        self.grid_alloc.Bind(gridlib.EVT_GRID_SELECT_CELL, self.on_select_alloc)
        self.btn_export.Bind(wx.EVT_BUTTON, self.on_export)

    def on_add(self, evt):
        self.grid.AppendRows(1)
        r = self.grid.GetNumberRows() - 1
        self.grid.SetRowSize(r, 32)
        self.grid.SetCellValue(r, 0, f"net{r+1}")
        self.grid.SetCellValue(r, 1, "50")

    def on_del(self, evt):
        rows = self.grid.GetSelectedRows()
        if not rows:
            return
        for r in sorted(rows, reverse=True):
            self.grid.DeleteRows(r, 1)

    def on_calc(self, evt):
        base = self.txt_base.GetValue().strip()
        if not validators.is_network_cidr(base):
            self.out.SetValue("Invalid base network CIDR. Example: 10.20.0.0/20")
            return
        demands = []
        for r in range(self.grid.GetNumberRows()):
            name = self.grid.GetCellValue(r, 0).strip() or f"net{r+1}"
            try:
                hosts = int(self.grid.GetCellValue(r, 1).strip())
            except ValueError:
                continue
            if hosts <= 0:
                continue
            demands.append({"name": name, "hosts": hosts})
        if not demands:
            self.out.SetValue("Please add at least one subnet row with hosts > 0.")
            return

        plan = vlsm.allocate_vlsm(base, demands)
        if not plan["ok"]:
            self.out.SetValue("Allocation failed: " + plan["error"])
            return

        # Populate summary grid
        self.grid_alloc.ClearGrid()
        # reset rows count
        if self.grid_alloc.GetNumberRows():
            self.grid_alloc.DeleteRows(0, self.grid_alloc.GetNumberRows())
        self.alloc_blocks = plan["blocks"]
        for blk in self.alloc_blocks:
            n = ip_network(blk["cidr"], strict=True)
            first, last = self._first_last(n)
            r = self.grid_alloc.GetNumberRows()
            self.grid_alloc.AppendRows(1)
            self.grid_alloc.SetCellValue(r, 0, blk["name"])
            self.grid_alloc.SetCellValue(r, 1, blk["cidr"])
            self.grid_alloc.SetCellValue(r, 2, str(blk["usable_hosts"]))
            self.grid_alloc.SetCellValue(r, 3, blk["gateway"])
            self.grid_alloc.SetCellValue(r, 4, first or "")
            self.grid_alloc.SetCellValue(r, 5, last or "")

        # Text summary
        lines = [f"Base: {base}", "Allocated:"]
        for blk in plan["blocks"]:
            lines.append(f" - {blk['name']:<10} {blk['cidr']:<18} hosts≈{blk['usable_hosts']} gw={blk['gateway']}")
        if plan["gaps"]:
            lines.append("Gaps:")
            for g in plan["gaps"]:
                lines.append(f"   {g}")
        self.out.SetValue("\\n".join(lines))

        # Select first block to load IPs
        if self.grid_alloc.GetNumberRows() > 0:
            self.grid_alloc.SetGridCursor(0,0)
            self.on_select_alloc(None)

    def _first_last(self, net):
        # Determine first/last usable depending on prefix
        if net.prefixlen == 32:
            ip = str(net.network_address)
            return ip, ip
        elif net.prefixlen == 31:
            hosts = list(net.hosts())
            return str(hosts[0]), str(hosts[1])
        else:
            hosts = list(net.hosts())
            if not hosts:
                return None, None
            return str(hosts[0]), str(hosts[-1])

    def on_select_alloc(self, evt):
        row = self.grid_alloc.GetGridCursorRow()
        if row < 0 or row >= self.grid_alloc.GetNumberRows():
            return
        cidr = self.grid_alloc.GetCellValue(row, 1)
        gw = self.grid_alloc.GetCellValue(row, 3)
        self.load_ips_for_subnet(cidr, gw)

    def load_ips_for_subnet(self, cidr: str, gateway: str):
        n = ip_network(cidr, strict=True)
        # Compute generator of usable IPs
        def gen_hosts():
            if n.prefixlen == 32:
                yield n.network_address
            elif n.prefixlen == 31:
                for h in n.hosts():
                    yield h
            else:
                for h in n.hosts():
                    yield h

        limit = int(self.spin_max.GetValue() or 4096)
        # reset grid
        if self.grid_ips.GetNumberRows():
            self.grid_ips.DeleteRows(0, self.grid_ips.GetNumberRows())
        count = 0
        for ip in gen_hosts():
            flag = "gateway" if str(ip) == gateway else ""
            r = self.grid_ips.GetNumberRows()
            self.grid_ips.AppendRows(1)
            self.grid_ips.SetCellValue(r, 0, str(ip))
            self.grid_ips.SetCellValue(r, 1, flag)
            count += 1
            if count >= limit:
                break
        if count >= limit:
            # add a note row
            r = self.grid_ips.GetNumberRows()
            self.grid_ips.AppendRows(1)
            self.grid_ips.SetCellValue(r, 0, f"... ({n.num_addresses} total addresses; showing first {limit} usable entries)")
            self.grid_ips.SetCellValue(r, 1, "")

    def on_export(self, evt):
        row = self.grid_alloc.GetGridCursorRow()
        if row < 0 or row >= self.grid_alloc.GetNumberRows():
            return
        cidr = self.grid_alloc.GetCellValue(row, 1)
        gw = self.grid_alloc.GetCellValue(row, 3)
        with wx.FileDialog(self, "Export IPs to CSV", wildcard="CSV files (*.csv)|*.csv",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            path = dlg.GetPath()
        # create CSV
        import csv
        n = ip_network(cidr, strict=True)
        limit = int(self.spin_max.GetValue() or 4096)
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ip", "flags"])
            count = 0
            if n.prefixlen == 32:
                w.writerow([str(n.network_address), "gateway" if str(n.network_address)==gw else ""])
            elif n.prefixlen == 31:
                for h in n.hosts():
                    if count >= limit: break
                    w.writerow([str(h), "gateway" if str(h)==gw else ""])
                    count += 1
            else:
                for h in n.hosts():
                    if count >= limit: break
                    w.writerow([str(h), "gateway" if str(h)==gw else ""])
                    count += 1
