"""
distribsim/ui/comparison.py
Tab Perbandingan Model Komunikasi.

Menampilkan ringkasan metrik ketiga model secara berdampingan,
tabel perbandingan karakteristik teknis, dan analisis kapan
menggunakan masing-masing model.

Data metrik diambil dari distribsim.data_models.metrics (global state)
dan di-refresh otomatis setiap 2 detik oleh DistribSimApp.
"""

import tkinter as tk

from ..data_models import metrics
from ..config import (
    BG_ROOT, BG_PANEL, BG_CARD, BG_DARK,
    BORDER, TEXT_1, TEXT_2, TEXT_3,
    COLOR_RR, COLOR_PS, COLOR_RPC,
    COLOR_OK, COLOR_ERR,
)
from ..utils import blend_color, fmt_ms


class ComparisonTab(tk.Frame):
    """
    Tab perbandingan: menampilkan metrik dan karakteristik ketiga model.

    Layout:
    1. Summary cards (RR | PS | RPC) — metrik real-time
    2. Tabel karakteristik teknis
    3. Analisis: kapan menggunakan masing-masing model
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_ROOT, **kwargs)
        # Referensi ke RPC simulation (di-set dari app.py)
        self._rpc_sim_ref = None
        self._build()

    def set_rpc_sim(self, rpc_sim):
        """Simpan referensi ke RPC simulation untuk baca RTT data."""
        self._rpc_sim_ref = rpc_sim

    def _build(self):
        # ---- Judul ----
        tk.Label(
            self, text="Perbandingan Model Komunikasi",
            bg=BG_ROOT, fg=TEXT_1, font=("Inter", 14, "bold")
        ).pack(pady=(16, 4))
        tk.Label(
            self, text="Jalankan simulasi di tiap tab untuk mengisi data secara real-time.",
            bg=BG_ROOT, fg=TEXT_2, font=("Inter", 9)
        ).pack(pady=(0, 14))

        self._build_summary_cards()
        self._build_comparison_table()
        self._build_analysis_cards()

    def _build_summary_cards(self):
        """Buat 3 kartu ringkasan metrik (RR, PS, RPC)."""
        frame = tk.Frame(self, bg=BG_ROOT)
        frame.pack(fill="x", padx=20, pady=(0, 14))

        self.card_labels = {}
        card_defs = [
            ("rr",  "⇄  Request-Response", COLOR_RR,
             [("Total Request", "—"), ("Avg Latency", "—"),
              ("Throughput", "—"), ("Success Rate", "—")]),
            ("ps",  "◎  Publish-Subscribe", COLOR_PS,
             [("Total Publish", "—"), ("Total Delivered", "—"),
              ("Throughput", "—"), ("Delivery Rate", "—")]),
            ("rpc", "⟳  RPC", COLOR_RPC,
             [("Total Panggilan", "—"), ("Avg RTT", "—"),
              ("Success Rate", "—"), ("Timeout Count", "—")]),
        ]

        for key, title, color, rows in card_defs:
            card = tk.Frame(frame, bg=BG_CARD,
                            highlightthickness=1, highlightbackground=BORDER)
            card.pack(side="left", fill="both", expand=True, padx=6)

            # Header berwarna
            hdr_bg = blend_color(color, 0.18, "#111326")
            hdr = tk.Frame(card, bg=hdr_bg, pady=6)
            hdr.pack(fill="x")
            tk.Label(hdr, text=title, bg=hdr_bg, fg=color,
                     font=("Inter", 10, "bold")).pack()

            # Baris metrik
            self.card_labels[key] = []
            for label, val in rows:
                row = tk.Frame(card, bg=BG_CARD)
                row.pack(fill="x", pady=2, padx=10)
                tk.Label(row, text=label, bg=BG_CARD, fg=TEXT_2,
                         font=("Inter", 8)).pack(side="left")
                v = tk.Label(row, text=val, bg=BG_CARD, fg=TEXT_1,
                             font=("Consolas", 8, "bold"))
                v.pack(side="right")
                self.card_labels[key].append(v)
            tk.Frame(card, bg=BG_CARD, height=6).pack()

    def _build_comparison_table(self):
        """Buat tabel karakteristik teknis ketiga model."""
        tbl_frame = tk.Frame(self, bg=BG_CARD,
                             highlightthickness=1, highlightbackground=BORDER)
        tbl_frame.pack(fill="x", padx=20, pady=(0, 14))
        tk.Label(
            tbl_frame, text="📊  Tabel Perbandingan Karakteristik",
            bg=BG_CARD, fg=TEXT_1, font=("Inter", 10, "bold"), pady=8
        ).pack()

        cols = ["Karakteristik", "Request-Response", "Publish-Subscribe", "RPC"]
        col_colors = [TEXT_2, COLOR_RR, COLOR_PS, COLOR_RPC]
        rows_data = [
            ("Pola Komunikasi",    "Sinkron (1:1)",       "Asinkron (1:N)",         "Sinkron (1:1)"),
            ("Coupling",           "🔴 Tinggi",            "🟢 Rendah",              "🔴 Tinggi"),
            ("Skalabilitas",       "⭐⭐",                "⭐⭐⭐⭐⭐",              "⭐⭐⭐"),
            ("Fault Tolerance",    "Manual retry",         "Built-in (queue)",       "Retry + timeout"),
            ("Overhead Jaringan",  "Rendah",               "Sedang (broker)",        "Sedang (marshal)"),
            ("Use Case",           "REST API, CRUD",       "IoT, Events, Streaming", "Microservices, gRPC"),
            ("Contoh Protokol",    "HTTP, WebSocket",      "MQTT, AMQP, Kafka",      "gRPC, XML-RPC"),
        ]

        grid = tk.Frame(tbl_frame, bg=BG_CARD)
        grid.pack(padx=10, pady=(0, 10))

        for ci, (col, cc) in enumerate(zip(cols, col_colors)):
            tk.Label(
                grid, text=col, bg="#0c0e1a", fg=cc,
                font=("Inter", 8, "bold"), width=22, anchor="w",
                padx=6, pady=4,
            ).grid(row=0, column=ci, padx=1, pady=1, sticky="ew")

        for ri, row in enumerate(rows_data):
            bg = BG_DARK if ri % 2 == 0 else "#0a0c14"
            for ci, cell in enumerate(row):
                tk.Label(
                    grid, text=cell, bg=bg,
                    fg=TEXT_1 if ci > 0 else TEXT_2,
                    font=("Inter", 8), width=22, anchor="w", padx=6, pady=3,
                ).grid(row=ri + 1, column=ci, padx=1, pady=1, sticky="ew")

    def _build_analysis_cards(self):
        """Buat 3 kartu analisis kapan menggunakan setiap model."""
        frame = tk.Frame(self, bg=BG_ROOT)
        frame.pack(fill="x", padx=20, pady=(0, 20))

        analyses = [
            ("🎯 Kapan Request-Response?",
             "Gunakan saat perlu respons langsung, transaksi tunggal yang jelas,\n"
             "atau ketika debugging diprioritaskan. Ideal untuk CRUD & REST API.\n"
             "Contoh: Web browser ↔ Backend server, Mobile app ↔ API gateway."),
            ("📡 Kapan Publish-Subscribe?",
             "Gunakan untuk event-driven architecture, distribusi data ke banyak\n"
             "konsumen, sistem IoT, atau high-throughput streaming data.\n"
             "Contoh: Sensor IoT, notifikasi real-time, data pipeline Kafka."),
            ("⚡ Kapan Remote Procedure Call?",
             "Gunakan saat ingin abstraksi remote seperti pemanggilan lokal,\n"
             "microservices yang saling berinteraksi, atau type-safety (gRPC).\n"
             "Contoh: Inter-service calls, gRPC microservices, CORBA legacy."),
        ]
        for title, body in analyses:
            f = tk.Frame(frame, bg=BG_CARD,
                         highlightthickness=1, highlightbackground=BORDER)
            f.pack(side="left", fill="both", expand=True, padx=6)
            tk.Label(f, text=title, bg=BG_CARD, fg=TEXT_1,
                     font=("Inter", 9, "bold"), pady=8).pack(anchor="w", padx=10)
            tk.Label(f, text=body, bg=BG_CARD, fg=TEXT_2,
                     font=("Inter", 8), justify="left").pack(anchor="w", padx=10, pady=(0, 10))

    # ----------------------------------------------------------------
    # Public: Refresh Metrik
    # ----------------------------------------------------------------

    def refresh(self):
        """
        Perbarui semua summary card dengan data metrik terkini.
        Dipanggil otomatis setiap 2 detik oleh DistribSimApp.
        """
        m_rr  = metrics["rr"]
        m_ps  = metrics["ps"]
        m_rpc = metrics["rpc"]

        # --- RR card ---
        avg_rr  = fmt_ms(sum(m_rr.latencies) / len(m_rr.latencies)) if m_rr.latencies else "—"
        rr_vals = [
            str(m_rr.total),
            avg_rr,
            f"{m_rr.throughput:.2f} req/s",
            f"{(m_rr.success / m_rr.total * 100):.0f}%" if m_rr.total else "—",
        ]
        for lbl, val in zip(self.card_labels["rr"], rr_vals):
            lbl.config(text=val)

        # --- PS card ---
        ps_vals = [
            str(m_ps.total),
            str(m_ps.delivered),
            f"{m_ps.throughput:.2f} msg/s",
            f"{min(m_ps.delivered / (m_ps.total * 2.5) * 100, 100):.0f}%"
            if m_ps.total else "—",
        ]
        for lbl, val in zip(self.card_labels["ps"], ps_vals):
            lbl.config(text=val)

        # --- RPC card ---
        rpc_rtts     = self._rpc_sim_ref.rpc_rtts     if self._rpc_sim_ref else []
        rpc_timeouts = self._rpc_sim_ref.rpc_timeouts  if self._rpc_sim_ref else 0
        avg_rpc = fmt_ms(sum(rpc_rtts) / len(rpc_rtts)) if rpc_rtts else "—"
        rpc_vals = [
            str(m_rpc.total),
            avg_rpc,
            f"{(m_rpc.success / m_rpc.total * 100):.0f}%" if m_rpc.total else "—",
            str(rpc_timeouts),
        ]
        for lbl, val in zip(self.card_labels["rpc"], rpc_vals):
            lbl.config(text=val)
