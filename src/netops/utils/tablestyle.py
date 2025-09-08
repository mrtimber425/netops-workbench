import wx
import wx.grid as gridlib

def style_grid(g: "gridlib.Grid", row_h: int = 32, def_col_w: int = 140, header_h: int = 28, rowlabel_w: int = 30):
    """Apply consistent sizing to a wx.Grid."""
    try:
        g.SetDefaultRowSize(row_h, True)
        g.SetDefaultColSize(def_col_w, True)
        g.SetColLabelSize(header_h)
        g.SetRowLabelSize(rowlabel_w)
    except Exception:
        pass
