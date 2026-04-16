import tkinter as tk
from distribsim.ui.app import DistribSimApp


def main():
    root = tk.Tk()

    # DPI awareness untuk tampilan lebih tajam di Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    DistribSimApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
