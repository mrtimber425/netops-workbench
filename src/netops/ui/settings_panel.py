import wx

class SettingsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        s = wx.BoxSizer(wx.VERTICAL)
        f = wx.FlexGridSizer(0, 2, 8, 8)
        f.AddGrowableCol(1, 1)

        f.Add(wx.StaticText(self, label="Theme:"), 0)
        self.cmb_theme = wx.ComboBox(self, choices=["System", "Light", "Dark"])
        self.cmb_theme.SetSelection(0)
        f.Add(self.cmb_theme, 0, wx.EXPAND)

        f.Add(wx.StaticText(self, label="Nmap Path:"), 0)
        self.txt_nmap = wx.TextCtrl(self, value="nmap")
        f.Add(self.txt_nmap, 0, wx.EXPAND)

        f.Add(wx.StaticText(self, label="Rate Limit (pps):"), 0)
        self.txt_rate = wx.TextCtrl(self, value="100")
        f.Add(self.txt_rate, 0, wx.EXPAND)

        s.Add(f, 0, wx.ALL | wx.EXPAND, 12)

        s.Add(wx.StaticText(self, label="Settings are persisted in a simple config file (to be added)."), 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        self.SetSizer(s)
