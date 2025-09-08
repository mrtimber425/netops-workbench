import wx

class AutoSizeDVColsMixin:
    """Mixin to auto-size DataViewListCtrl columns proportionally to fill width."""
    def _bind_autosize(self, dv_ctrl: "wx.dataview.DataViewListCtrl"):
        self._dv_autosize_ctrl = dv_ctrl
        self._dv_autosize_ctrl.Bind(wx.EVT_SIZE, self._on_dv_size)

    def _on_dv_size(self, evt):
        evt.Skip()
        ctrl = self._dv_autosize_ctrl
        if not ctrl:
            return
        total_w = ctrl.GetClientSize().width
        cols = [c for c in ctrl.Columns]
        if not cols:
            return
        # Reserve 20px padding between cols; size last column to remainder
        fixed = 0
        for c in cols[:-1]:
            # keep current width but ensure minimum
            w = max(120, c.Width)
            fixed += w + 8
        rem = max(200, total_w - fixed - 16)
        try:
            cols[-1].Width = rem
        except Exception:
            pass
