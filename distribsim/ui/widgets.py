"""
distribsim/ui/widgets.py
Widget UI bersama: LogWidget, tombol, slider, dropdown, panel metrik.
"""

import tkinter as tk
from tkinter import ttk
import time

from ..config import (
    BG_PANEL, BG_DARK,
    BORDER, TEXT_1, TEXT_2, TEXT_3,
    COLOR_RR, COLOR_OK, COLOR_ERR,
)
from ..utils import blend_color


class LogWidget(tk.Frame):
    """
    Area log real-time dengan warna berbeda per jenis pesan.
    Tag:  req (cyan) | res (hijau) | err (merah) | proc (kuning)
          pub (ungu) | rpc (hijau muda) | ts (abu — timestamp)
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_PANEL, **kwargs)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg="#0a0c1a", pady=4)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📋  Log Komunikasi",
                 bg="#0a0c1a", fg=TEXT_3,
                 font=("Inter", 8, "bold")).pack(side="left", padx=10)

        self.text = tk.Text(
            self, height=6, bg="#050610", fg=TEXT_2,
            font=("Consolas", 8), state="disabled",
            insertbackground=TEXT_1, selectbackground="#2a2d4a",
            wrap="word", relief="flat", padx=8, pady=4,
        )
        self.text.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.config(yscrollcommand=sb.set)

        from ..config import COLOR_PS, COLOR_RPC, COLOR_WARN
        self.text.tag_config("req",  foreground=COLOR_RR)
        self.text.tag_config("res",  foreground=COLOR_OK)
        self.text.tag_config("err",  foreground=COLOR_ERR)
        self.text.tag_config("proc", foreground=COLOR_WARN)
        self.text.tag_config("pub",  foreground=COLOR_PS)
        self.text.tag_config("rpc",  foreground=COLOR_RPC)
        self.text.tag_config("ts",   foreground=TEXT_3)

    def add(self, tag: str, text: str):
        """Tambah satu baris log."""
        ts = time.strftime("%H:%M:%S")
        self.text.config(state="normal")
        self.text.insert("end", f"[{ts}] ", "ts")
        self.text.insert("end", text + "\n", tag)
        self.text.see("end")
        lines = int(self.text.index("end-1c").split(".")[0])
        if lines > 100:
            self.text.delete("1.0", "3.0")
        self.text.config(state="disabled")

    def clear(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")


# ================================================================
# WIDGET FACTORIES
# ================================================================

def styled_button(parent, text, color=COLOR_RR, command=None, width=18):
    """Tombol dengan gaya dark theme. Returns (frame, button)."""
    f = tk.Frame(parent, bg=BG_PANEL)
    btn = tk.Button(
        f, text=text,
        bg=blend_color(color, 0.15, "#0d0f1c"), fg=color,
        activebackground=blend_color(color, 0.25, "#0d0f1c"), activeforeground=color,
        font=("Inter", 9, "bold"), relief="flat", bd=0,
        padx=12, pady=7, cursor="hand2", width=width, command=command,
        highlightthickness=1, highlightbackground=blend_color(color, 0.4),
    )
    btn.pack()
    return f, btn


def styled_scale(parent, from_, to, variable, command=None, color=COLOR_RR):
    """Slider dengan gaya dark theme."""
    return tk.Scale(
        parent, from_=from_, to=to, variable=variable,
        orient="horizontal", command=command,
        bg=BG_PANEL, fg=color, troughcolor="#1a1d2e",
        activebackground=color, highlightthickness=0,
        sliderrelief="flat", bd=0, font=("Consolas", 8),
    )


def styled_combo(parent, values, width=22):
    """Dropdown (Combobox) dengan gaya dark theme."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.TCombobox",
                    background=BG_DARK, foreground=TEXT_1,
                    fieldbackground="#0c0e1a", selectbackground="#1e2235",
                    arrowcolor=TEXT_2)
    cb = ttk.Combobox(parent, values=values, width=width,
                      style="Dark.TCombobox", state="readonly")
    cb.current(0)
    return cb


def build_metric_grid(parent, items):
    """
    Panel metrik real-time.
    items = list of (key, label_text, color)
    Returns: dict {key: tk.Label} untuk update nilai.
    """
    lbls  = {}
    frame = tk.Frame(parent, bg=BG_DARK, padx=8, pady=6)
    frame.pack(fill="x", pady=4)
    tk.Label(frame, text="METRIK REAL-TIME", bg=BG_DARK, fg=TEXT_3,
             font=("Inter", 7, "bold")).pack(anchor="w", pady=(0, 4))
    for key, lbl_text, color in items:
        row = tk.Frame(frame, bg=BG_DARK)
        row.pack(fill="x", pady=1)
        tk.Label(row, text=lbl_text, bg=BG_DARK, fg=TEXT_2,
                 font=("Inter", 8), width=14, anchor="w").pack(side="left")
        v = tk.Label(row, text="—", bg=BG_DARK, fg=color,
                     font=("Consolas", 8, "bold"))
        v.pack(side="right")
        lbls[key] = v
    return lbls
