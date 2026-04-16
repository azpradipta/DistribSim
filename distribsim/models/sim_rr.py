"""
distribsim/models/sim_rr.py
Simulasi Request-Response (HTTP/REST)

Pola: Sinkron, Point-to-Point (1:1)
Komponen: Client Node ↔ Server Node
Skenario: Web app mengirim HTTP request ke REST API
"""

import tkinter as tk
import random

from ..base_sim import BaseSimulation
from ..data_models import NodeDef, metrics, reset_metric
from ..utils import now, fmt_ms
from ..config import (
    CANVAS_H, CANVAS_W,
    COLOR_RR, COLOR_OK, COLOR_ERR, COLOR_WARN, COLOR_ACC,
    TEXT_1, TEXT_2, TEXT_3,
)


class RequestResponseSim(BaseSimulation):
    """
    Simulasi model Request-Response.
    Client mengirim request dan MENUNGGU (blocking) hingga server respons.
    """

    def __init__(self, canvas, log, lbl_total, lbl_success, lbl_fail,
                 lbl_latency, lbl_tp, lbl_rate, lbl_status):
        super().__init__(canvas)
        self.log  = log
        self.lbl  = {
            "total": lbl_total, "success": lbl_success, "fail": lbl_fail,
            "latency": lbl_latency, "tp": lbl_tp, "rate": lbl_rate,
            "status": lbl_status,
        }
        self.state     = "idle"
        self.ping_time = 0
        self.auto_id   = None
        self.auto_on   = False

        # Node sistem
        self.client = NodeDef(x=130, y=CANVAS_H // 2,
                              label="CLIENT", sublabel="Web App", color=COLOR_RR)
        self.server = NodeDef(x=CANVAS_W - 130, y=CANVAS_H // 2,
                              label="SERVER", sublabel="REST API", color=COLOR_ACC)

        # Variabel kontrol (di-set dari ui/app.py)
        self.latency_var = tk.IntVar(value=500)
        self.speed_var   = tk.DoubleVar(value=1.0)
        self.fail_var    = tk.BooleanVar(value=False)
        self.method_var  = tk.StringVar(value="GET")

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def send_request(self):
        """Kirim satu HTTP request; blok baru tidak bisa dikirim saat proses berlangsung."""
        if self.state != "idle":
            return

        m         = metrics["rr"]
        sp        = self.speed_var.get()
        lat       = self.latency_var.get()
        meth      = self.method_var.get()
        will_fail = self.fail_var.get() and random.random() < 0.3

        self.state        = "requesting"
        self.client.state = "active"
        self.server.state = "idle"
        self.ping_time    = now()

        # Throughput tracking
        if not m.tp_start:
            m.tp_start = now()
        m.tp_count += 1
        elapsed = (now() - m.tp_start) / 1000
        m.throughput = m.tp_count / elapsed if elapsed > 0 else 0

        self._set_status("active", f"Mengirim {meth} request...")
        self.log.add("req", f"→ HTTP {meth} /api/endpoint — mengirim...")

        pkt_speed = 0.006 * sp

        def on_req_arrive():
            self.client.state = "idle"
            if will_fail:
                self.server.state = "error"
                self.state        = "idle"
                m.total += 1; m.fail += 1
                self.log.add("err", "✗ 500 Internal Server Error — request gagal")
                self._set_status("error", "Server Error! Request gagal.")
                self.ptcl.spawn(self.server.x, self.server.y, COLOR_ERR, 12)
                self._update_metrics()
                self.canvas.after(2000, self._reset_status)
            else:
                self.server.state = "processing"
                self.state        = "processing"
                self.log.add("proc", f"⚙ Server memproses {meth} request...")
                self._set_status("processing", f"Server memproses (latensi: {lat}ms)...")
                self.canvas.after(int(lat / sp), _send_response)

        def _send_response():
            self.server.state = "active"
            self.state        = "responding"
            self.log.add("res", "← HTTP 200 OK — respons dikirim")

            def on_res_arrive():
                self.client.state = "active"
                self.server.state = "idle"
                self.state        = "idle"
                elapsed_ms = now() - self.ping_time
                m.total += 1; m.success += 1
                m.latencies.append(elapsed_ms)
                if len(m.latencies) > 50:
                    m.latencies.pop(0)
                self.ptcl.spawn(self.client.x, self.client.y, COLOR_OK, 10)
                self.log.add("res", f"✓ Response diterima — RTT: {fmt_ms(elapsed_ms)}")
                self._update_metrics()
                self._reset_status()
                self.canvas.after(800, lambda: setattr(self.client, "state", "idle"))

            self.spawn_packet(
                self.server.x, self.server.y, self.client.x, self.client.y,
                cx=(self.client.x + self.server.x) / 2, cy=self.client.y + 85,
                color=COLOR_OK, label="200", speed=pkt_speed, on_arrive=on_res_arrive,
            )

        self.spawn_packet(
            self.client.x, self.client.y, self.server.x, self.server.y,
            cx=(self.client.x + self.server.x) / 2, cy=self.client.y - 85,
            color=COLOR_RR, label=meth[:3], speed=pkt_speed, on_arrive=on_req_arrive,
        )

    def reset(self):
        """Reset ke kondisi awal."""
        self.packets = []
        self.state = "idle"
        self.client.state = "idle"
        self.server.state = "idle"
        reset_metric("rr")
        self._update_metrics()
        self._reset_status()
        self.log.clear()
        if self.auto_id:
            self.canvas.after_cancel(self.auto_id)
            self.auto_id = None
            self.auto_on = False

    def toggle_auto(self, enable: bool):
        """Aktifkan/matikan mode pengiriman otomatis."""
        self.auto_on = enable
        if enable:
            self._auto_loop()
        elif self.auto_id:
            self.canvas.after_cancel(self.auto_id)

    # ----------------------------------------------------------------
    # Private
    # ----------------------------------------------------------------

    def _auto_loop(self):
        if not self.auto_on:
            return
        self.send_request()
        self.auto_id = self.canvas.after(2200, self._auto_loop)

    def _set_status(self, state, text):
        colors = {"idle": TEXT_3, "active": COLOR_OK,
                  "processing": COLOR_WARN, "error": COLOR_ERR}
        self.lbl["status"].config(text=f"● {text}", fg=colors.get(state, TEXT_2))

    def _reset_status(self):
        self._set_status("idle", "Idle – Siap menerima request")

    def _update_metrics(self):
        m = metrics["rr"]
        self.lbl["total"].config(text=str(m.total))
        self.lbl["success"].config(text=str(m.success), fg=COLOR_OK)
        self.lbl["fail"].config(text=str(m.fail), fg=COLOR_ERR if m.fail else TEXT_1)
        avg = fmt_ms(sum(m.latencies) / len(m.latencies)) if m.latencies else "—"
        self.lbl["latency"].config(text=avg)
        self.lbl["tp"].config(text=f"{m.throughput:.2f} req/s")
        self.lbl["rate"].config(
            text=f"{(m.success / m.total * 100):.0f}%" if m.total else "—")

    # ----------------------------------------------------------------
    # Render
    # ----------------------------------------------------------------

    def render(self, t):
        c, s  = self.client, self.server
        mid_x = (c.x + s.x) / 2
        self.draw.draw_arrow_label(mid_x, c.y - 115, "REQUEST →", COLOR_RR)
        self.draw.draw_arrow_label(mid_x, s.y + 115, "← RESPONSE", COLOR_OK)
        self.draw.draw_connection(c.x, c.y, s.x, s.y, mid_x, c.y - 85, COLOR_RR)
        self.draw.draw_connection(s.x, s.y, c.x, c.y, mid_x, s.y + 85, COLOR_OK)
        if self.state == "processing":
            self.draw.draw_text_label(mid_x, CANVAS_H // 2,
                                      f"⚙ Processing {self.method_var.get()}...",
                                      COLOR_WARN, 9)
        self.draw.draw_node(c, t)
        self.draw.draw_node(s, t)
        self.draw.draw_text_label(30, 20, "Model: Request-Response", TEXT_3, 8)
        self.draw.draw_text_label(30, 35, "Pola: Sinkron 1:1", TEXT_3, 8)
