"""
distribsim/ui/app.py
Kelas utama aplikasi DistribSim (DistribSimApp).

Merakit semua tab, widget, dan simulasi menjadi satu window Tkinter:
  - Header aplikasi
  - Tab Request-Response (kontrol + canvas)
  - Tab Publish-Subscribe (kontrol + canvas)
  - Tab Remote Procedure Call (kontrol + canvas)
  - Tab Perbandingan (auto-refresh setiap 2 detik)
"""

import tkinter as tk
from tkinter import ttk

from ..config import (
    BG_ROOT, BG_PANEL, BG_DARK, BG_CARD,
    BORDER, TEXT_1, TEXT_2, TEXT_3,
    COLOR_RR, COLOR_PS, COLOR_RPC,
    COLOR_OK, COLOR_ERR, COLOR_WARN, COLOR_ACC,
    CANVAS_W, CANVAS_H,
)
from ..utils import blend_color
from .widgets import (
    LogWidget,
    styled_button, styled_scale, styled_combo,
    build_metric_grid,
)
from ..models.sim_rr  import RequestResponseSim
from ..models.sim_ps  import PubSubSim, TOPIC_COLORS
from ..models.sim_rpc import RPCSim, RPC_STEP_LABELS
from .comparison import ComparisonTab


class DistribSimApp:
    """
    Kelas utama aplikasi DistribSim.
    Merakit semua tab, widget, dan simulasi menjadi satu window.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self._configure_root()
        self._build_ui()
        self._start_comparison_refresh()

    # ================================================================
    # Setup
    # ================================================================

    def _configure_root(self):
        """Konfigurasi window dan tema ttk."""
        self.root.title("DistribSim – Simulasi Model Komunikasi Sistem Terdistribusi")
        self.root.configure(bg=BG_ROOT)
        self.root.geometry("1280x820")
        self.root.minsize(1100, 700)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG_ROOT, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#0d0f1c", foreground=TEXT_2,
            font=("Inter", 9, "bold"),
            padding=[14, 8], borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#111326")],
            foreground=[("selected", TEXT_1)],
        )
        style.configure("TFrame", background=BG_ROOT)
        style.configure("Vertical.TScrollbar",
                        background=BG_DARK, troughcolor=BG_ROOT, borderwidth=0)

    def _build_ui(self):
        """Bangun seluruh UI: header + tabs."""
        self._build_header()
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill="both", expand=True)
        self._build_rr_tab()
        self._build_ps_tab()
        self._build_rpc_tab()
        self._build_cmp_tab()

    # ================================================================
    # Header
    # ================================================================

    def _build_header(self):
        """Header aplikasi: logo, judul, badge tugas."""
        hdr = tk.Frame(self.root, bg="#090b15")
        hdr.pack(fill="x")
        inner = tk.Frame(hdr, bg="#090b15")
        inner.pack(fill="x", padx=20, pady=10)

        # Brand
        brand = tk.Frame(inner, bg="#090b15")
        brand.pack(side="left")
        tk.Label(brand, text="⬡", bg="#090b15", fg=COLOR_RR,
                 font=("Arial", 22)).pack(side="left", padx=(0, 10))
        title_f = tk.Frame(brand, bg="#090b15")
        title_f.pack(side="left")
        tk.Label(title_f, text="DistribSim", bg="#090b15", fg=TEXT_1,
                 font=("Inter", 16, "bold")).pack(anchor="w")
        tk.Label(title_f, text="Simulasi Interaktif Model Komunikasi Sistem Terdistribusi",
                 bg="#090b15", fg=TEXT_2, font=("Inter", 8)).pack(anchor="w")

        # Badge
        badge_bg = blend_color(COLOR_RR, 0.12, "#090b15")
        badge_bd = blend_color(COLOR_RR, 0.30, "#090b15")
        tk.Label(
            inner, text="  Tugas 2 · Sistem Paralel & Terdistribusi  ",
            bg=badge_bg, fg=COLOR_RR, font=("Inter", 8, "bold"),
            padx=10, pady=4, relief="flat",
            highlightthickness=1, highlightbackground=badge_bd,
        ).pack(side="right", padx=4)

        # Garis pemisah
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x")

    # ================================================================
    # Tab 1 — Request-Response
    # ================================================================

    def _build_rr_tab(self):
        """Bangun tab simulasi Request-Response."""
        tab = tk.Frame(self.nb, bg=BG_ROOT)
        self.nb.add(tab, text="  ⇄  Request-Response  ")

        paned = tk.PanedWindow(tab, orient="horizontal",
                               bg=BG_ROOT, sashwidth=4)
        paned.pack(fill="both", expand=True)

        # --- Panel kontrol kiri ---
        ctrl = tk.Frame(paned, bg=BG_PANEL, padx=10)
        paned.add(ctrl, minsize=220)

        tk.Label(ctrl, text="KONTROL", bg=BG_PANEL, fg=TEXT_3,
                 font=("Inter", 8, "bold")).pack(anchor="w", pady=(10, 8))

        # Metode HTTP
        tk.Label(ctrl, text="Metode HTTP:", bg=BG_PANEL, fg=TEXT_2,
                 font=("Inter", 8)).pack(anchor="w")
        self.rr_method = styled_combo(
            ctrl, ["GET /api/data", "POST /api/create",
                   "PUT /api/update/42", "DELETE /api/item/7"], width=24)
        self.rr_method.pack(anchor="w", pady=(2, 8))

        # Slider latensi
        self.rr_lat_var = tk.IntVar(value=500)
        tk.Label(ctrl, text="Latensi Server (ms):", bg=BG_PANEL, fg=TEXT_2,
                 font=("Inter", 8)).pack(anchor="w")
        self.rr_lat_lbl = tk.Label(ctrl, text="500 ms", bg=BG_PANEL, fg=COLOR_RR,
                                    font=("Consolas", 8, "bold"))
        self.rr_lat_lbl.pack(anchor="e")
        styled_scale(ctrl, 100, 3000, self.rr_lat_var,
                     command=lambda v: self.rr_lat_lbl.config(text=f"{int(float(v))} ms"),
                     color=COLOR_RR).pack(fill="x", pady=(0, 8))

        # Slider kecepatan animasi
        self.rr_spd_var = tk.DoubleVar(value=1.0)
        tk.Label(ctrl, text="Kecepatan Animasi:", bg=BG_PANEL, fg=TEXT_2,
                 font=("Inter", 8)).pack(anchor="w")
        self.rr_spd_lbl = tk.Label(ctrl, text="1.0×", bg=BG_PANEL, fg=COLOR_RR,
                                    font=("Consolas", 8, "bold"))
        self.rr_spd_lbl.pack(anchor="e")
        styled_scale(ctrl, 0.5, 4.0, self.rr_spd_var,
                     command=lambda v: self.rr_spd_lbl.config(text=f"{float(v):.1f}×"),
                     color=COLOR_RR).pack(fill="x", pady=(0, 8))

        # Checkbox simulasi kegagalan
        self.rr_fail_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl, text="Simulasi Kegagalan (30%)",
                       variable=self.rr_fail_var,
                       bg=BG_PANEL, fg=TEXT_2, selectcolor=BG_DARK,
                       activebackground=BG_PANEL, font=("Inter", 8)
                       ).pack(anchor="w", pady=(0, 4))

        # Checkbox mode otomatis
        self.rr_auto_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl, text="Mode Otomatis",
                       variable=self.rr_auto_var,
                       bg=BG_PANEL, fg=TEXT_2, selectcolor=BG_DARK,
                       activebackground=BG_PANEL, font=("Inter", 8),
                       command=self._rr_toggle_auto,
                       ).pack(anchor="w", pady=(0, 10))

        # Tombol
        btn_send, _ = styled_button(ctrl, "▶  Kirim Request", COLOR_RR, self._rr_send)
        btn_send.pack(fill="x", pady=2)
        btn_reset, _ = styled_button(ctrl, "↺  Reset", TEXT_2, self._rr_reset)
        btn_reset.pack(fill="x", pady=2)

        # Metrik
        met = build_metric_grid(ctrl, [
            ("total",   "Total Request",  TEXT_1),
            ("success", "Berhasil",       COLOR_OK),
            ("fail",    "Gagal",          COLOR_ERR),
            ("latency", "Avg Latensi",    TEXT_1),
            ("tp",      "Throughput",     TEXT_1),
            ("rate",    "Success Rate",   TEXT_1),
        ])

        # Label status
        self.rr_status = tk.Label(ctrl, text="● Idle – Siap menerima request",
                                   bg=BG_PANEL, fg=TEXT_3, font=("Inter", 8),
                                   wraplength=200, justify="left")
        self.rr_status.pack(anchor="w", pady=(8, 4))

        # Info box
        info = tk.Frame(ctrl, bg="#090b15", padx=8, pady=8)
        info.pack(fill="x", pady=(10, 0))
        tk.Label(info, text="ℹ  Request-Response", bg="#090b15", fg=COLOR_RR,
                 font=("Inter", 8, "bold")).pack(anchor="w")
        tk.Label(info, text="Komunikasi sinkron 1:1.\nClient menunggu respons\nsebelum melanjutkan.",
                 bg="#090b15", fg=TEXT_2, font=("Inter", 8), justify="left").pack(anchor="w")

        # --- Canvas + log kanan ---
        center = tk.Frame(paned, bg=BG_ROOT)
        paned.add(center, minsize=500)
        tk.Label(center, text="Visualisasi Aliran Komunikasi", bg=BG_ROOT, fg=TEXT_3,
                 font=("Inter", 8)).pack(anchor="w", padx=8, pady=(8, 2))
        self.rr_canvas = tk.Canvas(center, width=CANVAS_W, height=CANVAS_H,
                                    bg=BG_DARK, highlightthickness=1,
                                    highlightbackground=BORDER)
        self.rr_canvas.pack(fill="both", expand=True, padx=8, pady=4)
        self.rr_log = LogWidget(center)
        self.rr_log.pack(fill="x", padx=8, pady=(0, 8))

        # Init simulasi
        self.rr_sim = RequestResponseSim(
            self.rr_canvas, self.rr_log,
            met["total"], met["success"], met["fail"],
            met["latency"], met["tp"], met["rate"], self.rr_status,
        )
        self.rr_sim.latency_var = self.rr_lat_var
        self.rr_sim.speed_var   = self.rr_spd_var
        self.rr_sim.fail_var    = self.rr_fail_var
        self.rr_method.bind("<<ComboboxSelected>>",
                             lambda e: self.rr_sim.method_var.set(
                                 self.rr_method.get().split()[0]))
        self.rr_log.add("req", "🌐 Sistem Request-Response siap. Klik '▶ Kirim Request' untuk mulai.")
        self.rr_sim.start()

    def _rr_send(self):
        self.rr_sim.send_request()

    def _rr_reset(self):
        self.rr_sim.reset()
        self.rr_auto_var.set(False)

    def _rr_toggle_auto(self):
        self.rr_sim.toggle_auto(self.rr_auto_var.get())

    # ================================================================
    # Tab 2 — Publish-Subscribe
    # ================================================================

    def _build_ps_tab(self):
        """Bangun tab simulasi Publish-Subscribe."""
        tab = tk.Frame(self.nb, bg=BG_ROOT)
        self.nb.add(tab, text="  ◎  Publish-Subscribe  ")

        paned = tk.PanedWindow(tab, orient="horizontal",
                               bg=BG_ROOT, sashwidth=4)
        paned.pack(fill="both", expand=True)

        # --- Panel kontrol kiri ---
        ctrl = tk.Frame(paned, bg=BG_PANEL, padx=10)
        paned.add(ctrl, minsize=240)

        tk.Label(ctrl, text="KONTROL", bg=BG_PANEL, fg=TEXT_3,
                 font=("Inter", 8, "bold")).pack(anchor="w", pady=(10, 8))

        # Publisher
        tk.Label(ctrl, text="Publisher:", bg=BG_PANEL, fg=TEXT_2,
                 font=("Inter", 8)).pack(anchor="w")
        self.ps_pub = styled_combo(ctrl, [
            "Publisher 1 – Sensor Suhu",
            "Publisher 2 – Sensor Tekanan",
            "Publisher 3 – Sensor Kelembaban",
        ], width=26)
        self.ps_pub.pack(anchor="w", pady=(2, 8))

        # Topic
        tk.Label(ctrl, text="Topic:", bg=BG_PANEL, fg=TEXT_2,
                 font=("Inter", 8)).pack(anchor="w")
        self.ps_topic = styled_combo(
            ctrl, ["temperature", "pressure", "humidity", "alert"], width=26)
        self.ps_topic.pack(anchor="w", pady=(2, 8))

        # Payload
        tk.Label(ctrl, text="Payload:", bg=BG_PANEL, fg=TEXT_2,
                 font=("Inter", 8)).pack(anchor="w")
        self.ps_payload_var = tk.StringVar(value="24.5°C")
        tk.Entry(ctrl, textvariable=self.ps_payload_var,
                 bg=BG_DARK, fg=TEXT_1, insertbackground=TEXT_1,
                 font=("Consolas", 9), relief="flat",
                 highlightthickness=1, highlightbackground=BORDER,
                 width=24).pack(anchor="w", pady=(2, 8))

        # Slider kecepatan
        self.ps_spd_var = tk.DoubleVar(value=1.0)
        tk.Label(ctrl, text="Kecepatan Animasi:", bg=BG_PANEL, fg=TEXT_2,
                 font=("Inter", 8)).pack(anchor="w")
        self.ps_spd_lbl = tk.Label(ctrl, text="1.0×", bg=BG_PANEL, fg=COLOR_PS,
                                    font=("Consolas", 8, "bold"))
        self.ps_spd_lbl.pack(anchor="e")
        styled_scale(ctrl, 0.5, 4.0, self.ps_spd_var,
                     command=lambda v: self.ps_spd_lbl.config(text=f"{float(v):.1f}×"),
                     color=COLOR_PS).pack(fill="x", pady=(0, 10))

        # Tombol
        btn_pub, _ = styled_button(ctrl, "📤  Publish", COLOR_PS, self._ps_publish)
        btn_pub.pack(fill="x", pady=2)
        btn_auto_f, self.ps_auto_btn = styled_button(ctrl, "⚡  Auto Publish", COLOR_WARN,
                                                      self._ps_toggle_auto)
        btn_auto_f.pack(fill="x", pady=2)
        btn_rst, _ = styled_button(ctrl, "↺  Reset", TEXT_2, self._ps_reset)
        btn_rst.pack(fill="x", pady=2)

        # Metrik
        met = build_metric_grid(ctrl, [
            ("total",     "Total Publish",  TEXT_1),
            ("delivered", "Terkirim",       COLOR_OK),
            ("subs",      "Active Subs",    TEXT_1),
            ("tp",        "Throughput",     TEXT_1),
            ("rate",      "Delivery Rate",  TEXT_1),
        ])

        # Status
        self.ps_status = tk.Label(ctrl, text="● Idle – Sistem Pub-Sub aktif",
                                   bg=BG_PANEL, fg=TEXT_3, font=("Inter", 8),
                                   wraplength=210, justify="left")
        self.ps_status.pack(anchor="w", pady=(8, 4))

        # Subscription matrix
        mx = tk.Frame(ctrl, bg=BG_DARK, padx=6, pady=6)
        mx.pack(fill="x", pady=(8, 0))
        tk.Label(mx, text="SUBSCRIPTION MATRIX", bg=BG_DARK, fg=TEXT_3,
                 font=("Inter", 7, "bold")).pack(anchor="w", pady=(0, 4))
        grid_f = tk.Frame(mx, bg=BG_DARK)
        grid_f.pack(anchor="w")
        headers = ["Sub", "temp", "pres", "humi", "alert"]
        hcolors = [TEXT_2, TOPIC_COLORS["temperature"], TOPIC_COLORS["pressure"],
                   TOPIC_COLORS["humidity"], TOPIC_COLORS["alert"]]
        for ci, (h, hc) in enumerate(zip(headers, hcolors)):
            tk.Label(grid_f, text=h, bg=BG_DARK, fg=hc,
                     font=("Consolas", 7, "bold"), width=5
                     ).grid(row=0, column=ci, padx=1)
        matrix = [
            ("Sub-A", "✓", "✓", "✓", "✓"),
            ("Sub-B", "—", "—", "—", "✓"),
            ("Sub-C", "✓", "✓", "✓", "✓"),
            ("Sub-D", "✓", "—", "✓", "—"),
        ]
        for ri, row in enumerate(matrix):
            for ci, cell in enumerate(row):
                fg = COLOR_PS if cell == "✓" else TEXT_3
                tk.Label(grid_f, text=cell, bg=BG_DARK, fg=fg,
                         font=("Consolas", 7), width=5
                         ).grid(row=ri + 1, column=ci, padx=1, pady=1)

        # --- Canvas + log kanan ---
        center = tk.Frame(paned, bg=BG_ROOT)
        paned.add(center, minsize=500)
        tk.Label(center, text="Visualisasi Aliran Komunikasi", bg=BG_ROOT, fg=TEXT_3,
                 font=("Inter", 8)).pack(anchor="w", padx=8, pady=(8, 2))
        self.ps_canvas = tk.Canvas(center, width=CANVAS_W, height=CANVAS_H,
                                    bg=BG_DARK, highlightthickness=1,
                                    highlightbackground=BORDER)
        self.ps_canvas.pack(fill="both", expand=True, padx=8, pady=4)
        self.ps_log = LogWidget(center)
        self.ps_log.pack(fill="x", padx=8, pady=(0, 8))

        # Init simulasi
        self.ps_sim = PubSubSim(
            self.ps_canvas, self.ps_log,
            met["total"], met["delivered"], met["subs"],
            met["tp"], met["rate"], self.ps_status,
        )
        self.ps_sim.speed_var   = self.ps_spd_var
        self.ps_sim.payload_var = self.ps_payload_var
        self.ps_pub.bind("<<ComboboxSelected>>",
                          lambda e: self.ps_sim.pub_var.set(str(self.ps_pub.current())))
        self.ps_topic.bind("<<ComboboxSelected>>",
                            lambda e: self.ps_sim.topic_var.set(self.ps_topic.get()))
        self.ps_log.add("pub", "📡 Sistem Pub-Sub siap. Publisher & Subscriber terdaftar.")
        self.ps_sim.start()

    def _ps_publish(self):
        self.ps_sim.pub_var.set(str(self.ps_pub.current()))
        self.ps_sim.topic_var.set(self.ps_topic.get())
        self.ps_sim.publish()

    def _ps_toggle_auto(self):
        self.ps_sim.toggle_auto()
        self.ps_auto_btn.config(
            text="⏹  Stop Auto" if self.ps_sim.auto_on else "⚡  Auto Publish"
        )

    def _ps_reset(self):
        self.ps_sim.reset()
        self.ps_auto_btn.config(text="⚡  Auto Publish")

    # ================================================================
    # Tab 3 — Remote Procedure Call
    # ================================================================

    def _build_rpc_tab(self):
        """Bangun tab simulasi RPC."""
        tab = tk.Frame(self.nb, bg=BG_ROOT)
        self.nb.add(tab, text="  ⟳  Remote Procedure Call  ")

        paned = tk.PanedWindow(tab, orient="horizontal",
                               bg=BG_ROOT, sashwidth=4)
        paned.pack(fill="both", expand=True)

        # --- Panel kontrol kiri ---
        ctrl = tk.Frame(paned, bg=BG_PANEL, padx=10)
        paned.add(ctrl, minsize=240)

        tk.Label(ctrl, text="KONTROL", bg=BG_PANEL, fg=TEXT_3,
                 font=("Inter", 8, "bold")).pack(anchor="w", pady=(10, 8))

        # Pilihan fungsi RPC
        tk.Label(ctrl, text="Prosedur Remote:", bg=BG_PANEL, fg=TEXT_2,
                 font=("Inter", 8)).pack(anchor="w")
        self.rpc_fn = styled_combo(ctrl, [
            "getUser(userId=42) → User",
            "calculateSum(10, 20) → 30",
            'getWeather("Jakarta") → Data',
            "processOrder(id=101) → Receipt",
        ], width=28)
        self.rpc_fn.pack(anchor="w", pady=(2, 8))

        # Slider kecepatan
        self.rpc_spd_var = tk.DoubleVar(value=1.0)
        tk.Label(ctrl, text="Kecepatan Animasi:", bg=BG_PANEL, fg=TEXT_2,
                 font=("Inter", 8)).pack(anchor="w")
        self.rpc_spd_lbl = tk.Label(ctrl, text="1.0×", bg=BG_PANEL, fg=COLOR_RPC,
                                     font=("Consolas", 8, "bold"))
        self.rpc_spd_lbl.pack(anchor="e")
        styled_scale(ctrl, 0.5, 4.0, self.rpc_spd_var,
                     command=lambda v: self.rpc_spd_lbl.config(text=f"{float(v):.1f}×"),
                     color=COLOR_RPC).pack(fill="x", pady=(0, 8))

        # Checkbox timeout
        self.rpc_to_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl, text="Simulasi Timeout/Network Error",
                       variable=self.rpc_to_var,
                       bg=BG_PANEL, fg=TEXT_2, selectcolor=BG_DARK,
                       activebackground=BG_PANEL, font=("Inter", 8),
                       ).pack(anchor="w", pady=(0, 10))

        # Tombol
        btn_call, _ = styled_button(ctrl, "⚡  Panggil RPC", COLOR_RPC, self._rpc_call)
        btn_call.pack(fill="x", pady=2)
        btn_rst, _ = styled_button(ctrl, "↺  Reset", TEXT_2, self._rpc_reset)
        btn_rst.pack(fill="x", pady=2)

        # Metrik
        met = build_metric_grid(ctrl, [
            ("total",   "Total Panggilan", TEXT_1),
            ("success", "Berhasil",        COLOR_OK),
            ("timeout", "Timeout/Error",   COLOR_ERR),
            ("rtt",     "Avg RTT",         TEXT_1),
            ("rate",    "Success Rate",    TEXT_1),
        ])

        # Status
        self.rpc_status = tk.Label(ctrl, text="● Idle – Siap menerima panggilan RPC",
                                    bg=BG_PANEL, fg=TEXT_3, font=("Inter", 8),
                                    wraplength=210, justify="left")
        self.rpc_status.pack(anchor="w", pady=(8, 4))

        # Step tracker
        step_frame = tk.Frame(ctrl, bg=BG_DARK, padx=8, pady=8)
        step_frame.pack(fill="x", pady=(8, 0))
        tk.Label(step_frame, text="LANGKAH EKSEKUSI RPC", bg=BG_DARK, fg=TEXT_3,
                 font=("Inter", 7, "bold")).pack(anchor="w", pady=(0, 6))
        self.rpc_step_labels = []
        for i, step in enumerate(RPC_STEP_LABELS):
            f = tk.Frame(step_frame, bg=BG_DARK)
            f.pack(fill="x", pady=1)
            tk.Label(f, text=str(i + 1), bg=BG_DARK, fg=TEXT_3,
                     font=("Consolas", 7, "bold"), width=2).pack(side="left")
            lbl = tk.Label(f, text=step[3:], bg=BG_DARK, fg=TEXT_3,
                           font=("Inter", 8), anchor="w")
            lbl.pack(side="left")
            self.rpc_step_labels.append(lbl)

        # --- Canvas + log kanan ---
        center = tk.Frame(paned, bg=BG_ROOT)
        paned.add(center, minsize=500)
        tk.Label(center, text="Visualisasi Aliran Komunikasi", bg=BG_ROOT, fg=TEXT_3,
                 font=("Inter", 8)).pack(anchor="w", padx=8, pady=(8, 2))
        self.rpc_canvas = tk.Canvas(center, width=CANVAS_W, height=CANVAS_H,
                                     bg=BG_DARK, highlightthickness=1,
                                     highlightbackground=BORDER)
        self.rpc_canvas.pack(fill="both", expand=True, padx=8, pady=4)
        self.rpc_log = LogWidget(center)
        self.rpc_log.pack(fill="x", padx=8, pady=(0, 8))

        # Mapping indeks combo → nama fungsi
        self._rpc_fn_map = {
            0: "getUser", 1: "calculateSum",
            2: "getWeather", 3: "processOrder",
        }

        # Init simulasi
        self.rpc_sim = RPCSim(
            self.rpc_canvas, self.rpc_log,
            met["total"], met["success"], met["timeout"],
            met["rtt"], met["rate"], self.rpc_status,
            self.rpc_step_labels,
        )
        self.rpc_sim.speed_var   = self.rpc_spd_var
        self.rpc_sim.timeout_var = self.rpc_to_var
        self.rpc_fn.bind("<<ComboboxSelected>>",
                          lambda e: self.rpc_sim.fn_var.set(
                              self._rpc_fn_map.get(self.rpc_fn.current(), "getUser")))
        self.rpc_log.add("rpc", "⚡ Sistem RPC siap. Client Stub & Server Skeleton aktif.")
        self.rpc_sim.start()

    def _rpc_call(self):
        self.rpc_sim.fn_var.set(
            self._rpc_fn_map.get(self.rpc_fn.current(), "getUser"))
        self.rpc_sim.call_rpc()

    def _rpc_reset(self):
        self.rpc_sim.reset()

    # ================================================================
    # Tab 4 — Perbandingan
    # ================================================================

    def _build_cmp_tab(self):
        """Bangun tab perbandingan (scrollable)."""
        tab = tk.Frame(self.nb, bg=BG_ROOT)
        self.nb.add(tab, text="  ≡  Perbandingan  ")

        # Buat scrollable area
        canvas_wrap = tk.Canvas(tab, bg=BG_ROOT, highlightthickness=0)
        sb = ttk.Scrollbar(tab, orient="vertical", command=canvas_wrap.yview)
        canvas_wrap.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas_wrap.pack(side="left", fill="both", expand=True)

        self.cmp_tab = ComparisonTab(canvas_wrap)
        self.cmp_tab.set_rpc_sim(self.rpc_sim)
        canvas_wrap.create_window((0, 0), window=self.cmp_tab, anchor="nw")
        self.cmp_tab.bind(
            "<Configure>",
            lambda e: canvas_wrap.configure(scrollregion=canvas_wrap.bbox("all"))
        )

        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _on_tab_change(self, event):
        if self.nb.index(self.nb.select()) == 3:
            self.cmp_tab.refresh()

    def _start_comparison_refresh(self):
        """Auto-refresh tab perbandingan setiap 2 detik."""
        def loop():
            try:
                self.cmp_tab.refresh()
            except Exception:
                pass
            self.root.after(2000, loop)
        self.root.after(2000, loop)
