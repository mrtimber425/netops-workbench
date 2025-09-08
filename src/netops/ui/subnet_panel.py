import wx
from ..core import subnetting
from ..utils import validators

class SubnetPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        form = wx.FlexGridSizer(2, 3, 8, 8)
        form.AddGrowableCol(1, 1)

        self.txt_ip = wx.TextCtrl(self, value="10.0.0.1/24")
        btn_calc = wx.Button(self, label="Calculate")
        btn_calc.Bind(wx.EVT_BUTTON, self.on_calc)

        form.Add(wx.StaticText(self, label="IP/CIDR:"))
        form.Add(self.txt_ip, 1, wx.EXPAND)
        form.Add(btn_calc, 0)

        sizer.Add(form, 0, wx.ALL | wx.EXPAND, 12)

        self.out = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        font = self.out.GetFont()
        font.SetFaceName('Consolas' if 'Consolas' in wx.FontEnumerator().GetFacenames() else font.GetFaceName())
        self.out.SetFont(font)
        sizer.Add(self.out, 1, wx.ALL | wx.EXPAND, 12)

        self.SetSizer(sizer)

    def on_calc(self, evt):
        cidr = self.txt_ip.GetValue().strip()
        if not validators.is_cidr(cidr):
            self.out.SetValue("Invalid CIDR. Example: 10.0.0.1/22")
            return
        info = subnetting.describe_cidr(cidr)
        lines = [
            f"Input: {cidr}",
            f"Network: {info['network']}",
            f"Netmask: {info['netmask']}",
            f"Wildcard: {info['wildcard']}",
            f"Broadcast: {info['broadcast']}",
            f"Usable hosts: {info['usable_hosts']}",
            f"First usable: {info['first_usable']}",
            f"Last usable: {info['last_usable']}",
            f"/31 special-case: {info['is_31']}",
            f"/32 host-only: {info['is_32']}",
        ]
        self.out.SetValue("\n".join(lines))
