import wx
from .ui.main_frame import MainFrame
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dark", action="store_true", help="Enable dark theme (best effort).")
    args = parser.parse_args()

    app = wx.App(False)
    # Dark theme hint is OS-driven; hook custom theming later if needed.
    frame = MainFrame(None, title="NetOps Workbench")
    frame.Show()
    app.MainLoop()

if __name__ == "__main__":
    main()
