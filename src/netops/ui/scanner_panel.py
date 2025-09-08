import wx
import wx.dataview as dv
from ..utils.threads import run_in_thread, CancelToken
from ..core.scanner import icmp as icmp_scan
from ..core.scanner import arp as arp_scan
from ..core.scanner import nmap as nmap_scan
from ..utils.auto_dv import AutoSizeDVColsMixin

class ScannerPanel(wx.Panel, AutoSizeDVColsMixin):
    def __init__(self, parent):
        super().__init__(parent)
        self.cancel = None
        self._build()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        # Controls
        box = wx.StaticBoxSizer(wx.StaticBox(self, label="Targets & Modes"), wx.VERTICAL)
        row1 = wx.BoxSizer(wx.HORIZONTAL)
        row1.Add(wx.StaticText(self, label="Targets (CIDR or IP, comma separated):"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        self.txt_targets = wx.TextCtrl(self, value="192.168.1.0/24")
        row1.Add(self.txt_targets, 1, wx.RIGHT, 8)
        box.Add(row1, 0, wx.ALL | wx.EXPAND, 8)

        # Modes
        row2 = wx.BoxSizer(wx.HORIZONTAL)
        self.ck_arp = wx.CheckBox(self, label="ARP (LAN)")
        self.ck_icmp = wx.CheckBox(self, label="ICMP Ping")
        self.ck_nmap = wx.CheckBox(self, label="Nmap")
        self.ck_arp.SetValue(True)
        self.ck_icmp.SetValue(True)
        row2.Add(self.ck_arp, 0, wx.RIGHT, 12)
        row2.Add(self.ck_icmp, 0, wx.RIGHT, 12)
        row2.Add(self.ck_nmap, 0, wx.RIGHT, 12)
        box.Add(row2, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # Nmap options sub-box
        nmap_box = wx.FlexGridSizer(0, 6, 6, 8)
        nmap_box.AddGrowableCol(1, 1)
        nmap_box.AddGrowableCol(3, 1)
        nmap_box.AddGrowableCol(5, 1)

        nmap_box.Add(wx.StaticText(self, label="Scan type:"), 0)
        self.cmb_type = wx.ComboBox(self, choices=["SYN (-sS)", "Connect (-sT)", "UDP (-sU)"], style=wx.CB_READONLY)
        self.cmb_type.SetSelection(0)
        nmap_box.Add(self.cmb_type, 0, wx.EXPAND)

        self.chk_sV = wx.CheckBox(self, label="Service (-sV)")
        self.chk_sV.SetValue(True)
        nmap_box.Add(self.chk_sV, 0)

        self.chk_O = wx.CheckBox(self, label="OS (-O)")
        nmap_box.Add(self.chk_O, 0)

        self.chk_Pn = wx.CheckBox(self, label="No ping (-Pn)")
        nmap_box.Add(self.chk_Pn, 0)

        nmap_box.Add(wx.StaticText(self, label="Timing:"), 0)
        self.cmb_T = wx.ComboBox(self, choices=["T0","T1","T2","T3","T4","T5"], style=wx.CB_READONLY)
        self.cmb_T.SetSelection(3)  # T3
        nmap_box.Add(self.cmb_T, 0, wx.EXPAND)

        nmap_box.Add(wx.StaticText(self, label="Ports:"), 0)
        self.txt_ports = wx.TextCtrl(self, value="")  # empty -> use top ports
        nmap_box.Add(self.txt_ports, 0, wx.EXPAND)

        nmap_box.Add(wx.StaticText(self, label="Top ports:"), 0)
        self.txt_top = wx.TextCtrl(self, value="200")
        nmap_box.Add(self.txt_top, 0, wx.EXPAND)

        nmap_box.Add(wx.StaticText(self, label="Built command:"), 0)
        self.txt_cmd = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE)
        self.txt_cmd.SetMinSize((-1, 60))
        nmap_box.Add(self.txt_cmd, 0, wx.EXPAND)

        box.Add(nmap_box, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        # Run/Stop + progress
        row3 = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_run = wx.Button(self, label="Run")
        self.btn_stop = wx.Button(self, label="Stop")
        self.btn_stop.Disable()
        self.g_progress = wx.Gauge(self, range=100, style=wx.GA_HORIZONTAL)
        row3.Add(self.btn_run, 0, wx.RIGHT, 8)
        row3.Add(self.btn_stop, 0, wx.RIGHT, 12)
        row3.Add(self.g_progress, 1, wx.EXPAND)
        box.Add(row3, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

        root.Add(box, 0, wx.ALL | wx.EXPAND, 12)

        # Results list
        self.dv = dv.DataViewListCtrl(self, style=dv.DV_ROW_LINES | dv.DV_VERT_RULES)
        for col in ["Source", "IP", "MAC/RTT/OS", "Service/Info"]:
            self.dv.AppendTextColumn(col, width=180 if col!="Service/Info" else 380)
        root.Add(self.dv, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        self._bind_autosize(self.dv)

        # Log output
        self.out = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        root.Add(self.out, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)

        self.SetSizer(root)

        # Events
        self.btn_run.Bind(wx.EVT_BUTTON, self.on_run)
        self.btn_stop.Bind(wx.EVT_BUTTON, self.on_stop)

    # Thread-safe log
    def log(self, msg):
        wx.CallAfter(self.out.AppendText, msg + "\\n")

    def set_progress(self, pct):
        wx.CallAfter(self.g_progress.SetValue, max(0, min(100, int(pct))))

    def on_run(self, evt):
        targets = [t.strip() for t in self.txt_targets.GetValue().split(",") if t.strip()]
        if not targets:
            self.log("No targets provided.")
            return
        self.dv.DeleteAllItems()
        self.cancel = CancelToken()
        self.btn_run.Disable()
        self.btn_stop.Enable()
        self.set_progress(0)
        self.log("Starting scans...")
        run_in_thread(self._do_scan, targets, self.cancel)

    def on_stop(self, evt):
        if self.cancel:
            self.cancel.cancel()
            self.log("Cancelling...")

    def _do_scan(self, targets, token):
        import wx
        total_steps = 0
        steps_done = 0

        icmp_ips = icmp_scan.expand_targets(targets) if self.ck_icmp.IsChecked() else []
        total_steps += len(icmp_ips)
        total_steps += len(targets) if self.ck_arp.IsChecked() else 0
        total_steps += 1 if self.ck_nmap.IsChecked() else 0
        total_steps = max(total_steps, 1)

        # ICMP
        if self.ck_icmp.IsChecked():
            self.log("ICMP sweep running...")
            res = icmp_scan.ping_sweep(targets, timeout=1.0, max_workers=64)
            for r in res:
                if token.is_cancelled(): break
                src = "ICMP"
                ip = r["host"]
                meta = f"UP rtt={r['rtt_ms']:.2f}ms" if r["up"] and r["rtt_ms"] is not None else ("UP" if r["up"] else "down")
                wx.CallAfter(self.dv.AppendItem, [src, ip, meta, ""])
                steps_done += 1
                self.set_progress(steps_done * 100 / total_steps)

        # ARP
        if self.ck_arp.IsChecked():
            self.log("ARP scans running...")
            for t in targets:
                if token.is_cancelled(): break
                r = arp_scan.arp_scan(t, timeout=2.0)
                if not r["ok"]:
                    self.log(f"ARP error for {t}: {r['error']}")
                else:
                    for h in r["hosts"]:
                        if token.is_cancelled(): break
                        wx.CallAfter(self.dv.AppendItem, ["ARP", h["ip"], h["mac"], ""])
                steps_done += 1
                self.set_progress(steps_done * 100 / total_steps)

        # Nmap
        if self.ck_nmap.IsChecked():
            if not nmap_scan.has_nmap():
                self.log("Nmap not found in PATH. Skipping.")
            else:
                stype = {0:"syn",1:"connect",2:"udp"}.get(self.cmb_type.GetSelection(), "syn")
                ports = self.txt_ports.GetValue().strip() or None
                try:
                    top_ports = int(self.txt_top.GetValue().strip() or "0") or None
                except Exception:
                    top_ports = 200
                r = nmap_scan.run_nmap_xml(
                    targets,
                    scan_type=stype,
                    service_version=self.chk_sV.IsChecked(),
                    os_detect=self.chk_O.IsChecked(),
                    no_ping=self.chk_Pn.IsChecked(),
                    top_ports=top_ports,
                    ports=ports,
                    timing=self.cmb_T.GetValue() or "T3",
                )
                self.log("Nmap cmd: " + r.get("cmd",""))
                if not r["ok"]:
                    self.log(f"Nmap error: {r['error']}")
                else:
                    for host in r["hosts"]:
                        meta = host.get("os") or ""
                        services = ", ".join([f"{s['proto']}/{s['port']} {s['name'] or ''} {s['product'] or ''} {s['version'] or ''}".strip() for s in host.get("services", []) if s.get("state") == "open"])
                        wx.CallAfter(self.dv.AppendItem, ["Nmap", host.get("ip") or "", meta, services])
                steps_done += 1
                self.set_progress(steps_done * 100 / total_steps)

        wx.CallAfter(self.btn_run.Enable)
        wx.CallAfter(self.btn_stop.Disable)
        self.set_progress(100)
        self.log("Scans finished.")
