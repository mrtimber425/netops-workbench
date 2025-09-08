import wx
import wx.aui as aui

from .subnet_panel import SubnetPanel
from .vlsm_panel import VLSMPanel
from .dns_panel import DNSPanel
from .firewall_panel import FirewallPanel
from .scanner_panel import ScannerPanel
from .reports_panel import ReportsPanel
from .packet_panel import PacketPanel
from .ios_panel import IOSPanel
from .settings_panel import SettingsPanel

class MainFrame(wx.Frame):
    def __init__(self, parent, title="NetOps Workbench"):
        super().__init__(parent, title=title, size=(1280, 860))
        self._mgr = aui.AuiManager(self)
        self._build_ui()
        self.CreateStatusBar()
        self.SetStatusText("Ready.")

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def _build_ui(self):
        # Sidebar
        self.tree = wx.TreeCtrl(self, style=wx.TR_HAS_BUTTONS | wx.TR_DEFAULT_STYLE)
        root = self.tree.AddRoot("Modules")
        self.nodes = {}
        for name in ["Subnet Planner", "VLSM Designer", "DNS Toolkit", "Firewall Simulator", "Scanner", "PCAP Analyzer", "IOS Helper", "Reports", "Settings"]:
            self.nodes[name] = self.tree.AppendItem(root, name)
        self.tree.ExpandAll()

        # Notebook for panels
        self.nb = aui.AuiNotebook(self, style=aui.AUI_NB_TAB_SPLIT | aui.AUI_NB_TAB_MOVE | aui.AUI_NB_SCROLL_BUTTONS)
        self.pages = {}

        self.pages["Subnet Planner"] = SubnetPanel(self.nb)
        self.nb.AddPage(self.pages["Subnet Planner"], "Subnet Planner")

        self.pages["VLSM Designer"] = VLSMPanel(self.nb)
        self.nb.AddPage(self.pages["VLSM Designer"], "VLSM Designer")

        self.pages["DNS Toolkit"] = DNSPanel(self.nb)
        self.nb.AddPage(self.pages["DNS Toolkit"], "DNS Toolkit")

        self.pages["Firewall Simulator"] = FirewallPanel(self.nb)
        self.nb.AddPage(self.pages["Firewall Simulator"], "Firewall")

        self.pages["Scanner"] = ScannerPanel(self.nb)
        self.nb.AddPage(self.pages["Scanner"], "Scanner")
        self.pages["PCAP Analyzer"] = PacketPanel(self.nb)
        self.nb.AddPage(self.pages["PCAP Analyzer"], "PCAP Analyzer")

        self.pages["IOS Helper"] = IOSPanel(self.nb)
        self.nb.AddPage(self.pages["IOS Helper"], "IOS Helper")


        self.pages["Reports"] = ReportsPanel(self.nb)
        self.nb.AddPage(self.pages["Reports"], "Reports")

        self.pages["Settings"] = SettingsPanel(self.nb)
        self.nb.AddPage(self.pages["Settings"], "Settings")

        # Layout manager
        self._mgr.AddPane(self.tree, aui.AuiPaneInfo().Left().Caption("Navigation").BestSize((260, -1)).CloseButton(False).MinSize((200,-1)).Movable(True).Floatable(True).Dockable(True))
        self._mgr.AddPane(self.nb, aui.AuiPaneInfo().CenterPane())
        self._mgr.Update()

        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_select)

        # Menu
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        item_quit = file_menu.Append(wx.ID_EXIT, "E&xit\tCtrl-Q", "Quit")
        self.Bind(wx.EVT_MENU, lambda evt: self.Close(), item_quit)
        menubar.Append(file_menu, "&File")

        view_menu = wx.Menu()
        item_dark = view_menu.Append(wx.ID_ANY, "Toggle &Dark Hint")
        self.Bind(wx.EVT_MENU, self.on_dark_hint, item_dark)
        menubar.Append(view_menu, "&View")

        help_menu = wx.Menu()
        about = help_menu.Append(wx.ID_ABOUT, "&About")
        self.Bind(wx.EVT_MENU, self.on_about, about)
        menubar.Append(help_menu, "&Help")
        self.SetMenuBar(menubar)

    def on_tree_select(self, evt):
        item = evt.GetItem()
        label = self.tree.GetItemText(item)
        if label in self.pages:
            idx = list(self.pages.keys()).index(label)
            self.nb.ChangeSelection(idx)

    def on_dark_hint(self, evt):
        wx.MessageBox("Dark theme follows your OS theme. Custom theming can be added later.", "Theme", wx.OK | wx.ICON_INFORMATION)

    def on_about(self, evt):
        wx.MessageBox("NetOps Workbench\nA networking & net-sec toolkit (MVP)", "About", wx.OK | wx.ICON_INFORMATION)

    def on_close(self, evt):
        try:
            self._mgr.UnInit()
        finally:
            evt.Skip()
