"""
distribsim/models/sim_rpc.py
Simulasi Remote Procedure Call / RPC (gRPC/CORBA)

Pola: Sinkron-Transparan, Prosedural (1:1)
Komponen (5 node): CLIENT → C-STUB → NETWORK → S-SKEL → SERVER
Skenario: Microservice memanggil prosedur pada service lain secara transparan

Alur 7 langkah:
  1. Client memanggil fungsi lokal (stub)
  2. Stub marshal parameter → format jaringan
  3. Data dikirim via TCP/HTTP2
  4. Skeleton terima + unmarshal
  5. Server eksekusi prosedur
  6. Hasil di-marshal + dikirim balik
  7. Client terima hasil (seolah fungsi lokal)
"""

import tkinter as tk

from ..base_sim import BaseSimulation
from ..data_models import NodeDef, metrics, reset_metric
from ..utils import now, fmt_ms
from ..config import (
    CANVAS_H, CANVAS_W,
    COLOR_RR, COLOR_RPC, COLOR_OK, COLOR_ERR, COLOR_WARN, COLOR_ACC,
    TEXT_2, TEXT_3,
)

# ================================================================
# Konstanta RPC
# ================================================================

RPC_FUNCTIONS = {
    "getUser":      ("userId=42",   '{ id:42, name:"Ahmad Fariz" }'),
    "calculateSum": ("a=10, b=20",  "30"),
    "getWeather":   ('"Jakarta"',   '{ temp:32°C, humid:80% }'),
    "processOrder": ("orderId=101", '{ status:"confirmed" }'),
}

RPC_STEP_LABELS = [
    "1. Client memanggil fungsi lokal",
    "2. Stub: marshaling parameter",
    "3. Transmisi via TCP/HTTP2",
    "4. Skeleton: unmarshaling",
    "5. Server mengeksekusi prosedur",
    "6. Hasil di-marshal & dikirim",
    "7. Client menerima hasil akhir",
]

# (src_idx, dst_idx, color, label, arc_up)
RPC_STEP_PAIRS = [
    (0, 1, COLOR_RR,  "call",    True),
    (1, 2, "#fff176", "marshal", True),
    (2, 3, "#80cbc4", "send",    True),
    (3, 4, "#ff8a65", "invoke",  True),
    (4, 3, COLOR_ACC, "result",  False),
    (3, 2, "#ff8a65", "marshal", False),
    (2, 1, "#80cbc4", "recv",    False),
    (1, 0, "#fff176", "return",  False),
]


class RPCSim(BaseSimulation):
    """
    Simulasi model RPC.
    Transparansi jarak jauh: client memanggil remote seolah fungsi lokal.
    """

    def __init__(self, canvas, log, lbl_total, lbl_success, lbl_timeout,
                 lbl_rtt, lbl_rate, lbl_status, step_labels):
        super().__init__(canvas)
        self.log       = log
        self.lbl       = {
            "total": lbl_total, "success": lbl_success, "timeout": lbl_timeout,
            "rtt": lbl_rtt, "rate": lbl_rate, "status": lbl_status,
        }
        self.step_lbls    = step_labels
        self.busy         = False
        self.ping_time    = 0
        self.rpc_rtts: list  = []
        self.rpc_timeouts: int = 0

        # 5 node (horizontal)
        ys = CANVAS_H // 2
        specs = [
            (65,  "CLIENT",  "Caller",     COLOR_RR),
            (192, "C-STUB",  "Marshaler",  "#fff176"),
            (330, "NETWORK", "TCP/HTTP2",  "#80cbc4"),
            (468, "S-SKEL",  "Dispatcher", "#ff8a65"),
            (595, "SERVER",  "Executor",   COLOR_ACC),
        ]
        self.nodes = [NodeDef(x=x, y=ys, label=lbl, sublabel=sub, color=col, radius=32)
                      for x, lbl, sub, col in specs]

        # Variabel kontrol
        self.speed_var   = tk.DoubleVar(value=1.0)
        self.fn_var      = tk.StringVar(value="getUser")
        self.timeout_var = tk.BooleanVar(value=False)

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def call_rpc(self):
        """Jalankan satu siklus RPC penuh (8 langkah animasi)."""
        if self.busy:
            return
        self.busy  = True
        fn         = self.fn_var.get()
        sp         = self.speed_var.get()
        to_mode    = self.timeout_var.get()
        params, result = RPC_FUNCTIONS.get(fn, ("...", "..."))

        m = metrics["rpc"]
        m.total += 1
        self.ping_time = now()
        for nd in self.nodes:
            nd.state = "idle"

        self.log.add("rpc", f"⚡ Client calls: {fn}({params})")
        self._set_status("active", f"Memanggil {fn}()...")

        step_delay = int(320 / sp)

        def run_step(idx):
            if idx >= len(RPC_STEP_PAIRS):
                # Selesai
                elapsed = now() - self.ping_time
                m.success += 1
                self.rpc_rtts.append(elapsed)
                if len(self.rpc_rtts) > 50:
                    self.rpc_rtts.pop(0)
                for nd in self.nodes: nd.state = "idle"
                self.busy = False
                self._clear_steps()
                self.ptcl.spawn(self.nodes[0].x, self.nodes[0].y, COLOR_OK, 14)
                self.log.add("res",
                             f"✓ {fn}() selesai — Hasil: {result} — RTT: {fmt_ms(elapsed)}")
                self._set_status("idle", "Idle – Siap menerima panggilan RPC")
                self._update_metrics()
                return

            si, di, col, lbl, arc_up = RPC_STEP_PAIRS[idx]
            self._highlight_step(min(idx, 6))
            self.nodes[si].state = "active"

            src, dst = self.nodes[si], self.nodes[di]
            cy = src.y - 70 if arc_up else src.y + 70

            # Simulasi timeout di tengah pengiriman
            if to_mode and idx == 3:
                self._set_status("error", "TIMEOUT! Tidak ada respons dari server.")
                self.log.add("err", f"✗ TIMEOUT — {fn}() tidak mendapat respons")
                for nd in self.nodes: nd.state = "idle"
                self.rpc_timeouts += 1
                self.busy = False
                self._clear_steps()
                self.ptcl.spawn(self.nodes[2].x, self.nodes[2].y, COLOR_ERR, 14)
                self._update_metrics()
                return

            step_log = [
                f"Step 1: Client memanggil {fn}() → Client Stub",
                f"Step 2: Stub marshaling parameter: {params}",
                "Step 3: Request dikirim via jaringan...",
                "Step 4: Skeleton menerima & unmarshal",
                f"Step 5: Server mengeksekusi {fn}()",
                f"Step 6: Hasil di-marshal: {result}",
                "Step 7: Respons dikirim via jaringan",
                "Step 8: Client menerima hasil akhir",
            ]
            if idx < len(step_log):
                self.log.add("rpc", step_log[idx])

            def on_arrive(si=si, di=di, col=col, idx=idx):
                self.nodes[si].state = "idle"
                self.nodes[di].state = "processing"
                self.ptcl.spawn(dst.x, dst.y, col, 5)
                self.canvas.after(step_delay, lambda: run_step(idx + 1))

            self.spawn_packet(
                src.x, src.y, dst.x, dst.y,
                cx=(src.x + dst.x) / 2, cy=cy,
                color=col, label=lbl,
                speed=0.011 * sp, on_arrive=on_arrive, radius=8,
            )

        run_step(0)

    def reset(self):
        """Reset ke kondisi awal."""
        self.packets = []
        for nd in self.nodes: nd.state = "idle"
        self.busy          = False
        self.rpc_rtts      = []
        self.rpc_timeouts  = 0
        reset_metric("rpc")
        self._update_metrics()
        self._clear_steps()
        self._set_status("idle", "Idle – Siap menerima panggilan RPC")
        self.log.clear()

    # ----------------------------------------------------------------
    # Private
    # ----------------------------------------------------------------

    def _highlight_step(self, step_idx):
        for i, lbl in enumerate(self.step_lbls):
            if   i < step_idx:  lbl.config(fg=COLOR_OK,  font=("Inter", 8))
            elif i == step_idx: lbl.config(fg=COLOR_RPC, font=("Inter", 8, "bold"))
            else:               lbl.config(fg=TEXT_3,    font=("Inter", 8))

    def _clear_steps(self):
        for lbl in self.step_lbls:
            lbl.config(fg=TEXT_3, font=("Inter", 8))

    def _set_status(self, state, text):
        colors = {"idle": TEXT_3, "active": COLOR_OK,
                  "processing": COLOR_WARN, "error": COLOR_ERR}
        self.lbl["status"].config(text=f"● {text}", fg=colors.get(state, TEXT_2))

    def _update_metrics(self):
        m = metrics["rpc"]
        self.lbl["total"].config(text=str(m.total))
        self.lbl["success"].config(text=str(m.success), fg=COLOR_OK)
        self.lbl["timeout"].config(
            text=str(self.rpc_timeouts),
            fg=COLOR_ERR if self.rpc_timeouts else "#e8eaf6")
        avg = fmt_ms(sum(self.rpc_rtts) / len(self.rpc_rtts)) if self.rpc_rtts else "—"
        self.lbl["rtt"].config(text=avg)
        self.lbl["rate"].config(
            text=f"{(m.success / m.total * 100):.0f}%" if m.total else "—")

    # ----------------------------------------------------------------
    # Render
    # ----------------------------------------------------------------

    def render(self, t):
        step_lbl = ["1.Call", "2.Marshal", "3.Network", "4.Unmarshal", "5.Execute"]
        for i, nd in enumerate(self.nodes):
            c = nd.color if nd.state != "idle" else TEXT_3
            self.draw.draw_text_label(nd.x, nd.y - 50, step_lbl[i], c, 7)
        for i in range(len(self.nodes) - 1):
            a, b = self.nodes[i], self.nodes[i + 1]
            mx = (a.x + b.x) / 2
            self.draw.draw_connection(a.x, a.y, b.x, b.y, mx, a.y - 55, COLOR_RR, (6, 4))
            self.draw.draw_connection(b.x, b.y, a.x, a.y, mx, b.y + 55, COLOR_ACC, (6, 4))
            self.draw.draw_arrow_label(mx, self.nodes[0].y - 65, "→", COLOR_RR)
            self.draw.draw_arrow_label(mx, self.nodes[0].y + 65, "←", COLOR_ACC)
        for nd in self.nodes:
            self.draw.draw_node(nd, t)
        self.draw.draw_text_label(CANVAS_W // 2, 18, "Model: Remote Procedure Call", TEXT_3, 8)
        self.draw.draw_text_label(CANVAS_W // 2, 32, "Pola: Transparan, Prosedural", TEXT_3, 8)
