"""
distribsim/models/sim_ps.py
Simulasi Publish-Subscribe (MQTT/Kafka)

Pola: Asinkron, One-to-Many (1:N)
Komponen: 3 Publisher (sensor) → Broker → 4 Subscriber
Skenario: Sistem IoT mengirim data lingkungan ke berbagai konsumen

Subscription Matrix:
  Sub-A (Dashboard) : temperature, pressure, humidity, alert
  Sub-B (Alert Sys) : alert
  Sub-C (Logger)    : temperature, pressure, humidity, alert
  Sub-D (Actuator)  : temperature, humidity
"""

import tkinter as tk
import random

from ..base_sim import BaseSimulation
from ..data_models import NodeDef, metrics, reset_metric
from ..utils import now, fmt_ms
from ..config import (
    CANVAS_H, CANVAS_W,
    COLOR_PS, COLOR_OK, COLOR_ERR, COLOR_WARN, COLOR_RPC,
    TEXT_1, TEXT_2, TEXT_3,
)

# ================================================================
# Konstanta Pub-Sub
# ================================================================

TOPIC_COLORS = {
    "temperature": "#ef9a9a",
    "pressure":    "#ffe082",
    "humidity":    "#80deea",
    "alert":       "#ff8a65",
}

SUBSCRIBER_TOPICS = {
    "SUB-A": ["temperature", "pressure", "humidity", "alert"],
    "SUB-B": ["alert"],
    "SUB-C": ["temperature", "pressure", "humidity", "alert"],
    "SUB-D": ["temperature", "humidity"],
}


class PubSubSim(BaseSimulation):
    """
    Simulasi model Publish-Subscribe.
    Publisher tidak mengetahui siapa subscriber-nya.
    Broker yang merouting berdasarkan topic (loose coupling).
    """

    def __init__(self, canvas, log, lbl_total, lbl_delivered,
                 lbl_subs, lbl_tp, lbl_rate, lbl_status):
        super().__init__(canvas)
        self.log  = log
        self.lbl  = {
            "total": lbl_total, "delivered": lbl_delivered, "subs": lbl_subs,
            "tp": lbl_tp, "rate": lbl_rate, "status": lbl_status,
        }
        self.auto_on = False
        self.auto_id = None

        # Node sistem
        self.pubs = [
            NodeDef(x=90, y=105, label="PUB-1", sublabel="Sensor Suhu",
                    color=COLOR_RPC, radius=30),
            NodeDef(x=90, y=210, label="PUB-2", sublabel="Sensor Tekanan",
                    color="#81c784", radius=30),
            NodeDef(x=90, y=315, label="PUB-3", sublabel="Sensor Kelembaban",
                    color="#66bb6a", radius=30),
        ]
        self.broker = NodeDef(x=CANVAS_W // 2, y=CANVAS_H // 2,
                              label="BROKER", sublabel="Message Bus",
                              color=COLOR_PS, radius=46)
        self.subs = [
            NodeDef(x=CANVAS_W - 90, y=75,  label="SUB-A", sublabel="Dashboard",
                    color="#80deea", radius=28),
            NodeDef(x=CANVAS_W - 90, y=175, label="SUB-B", sublabel="Alert Sys",
                    color="#4dd0e1", radius=28),
            NodeDef(x=CANVAS_W - 90, y=275, label="SUB-C", sublabel="Logger",
                    color="#26c6da", radius=28),
            NodeDef(x=CANVAS_W - 90, y=365, label="SUB-D", sublabel="Actuator",
                    color="#00bcd4", radius=28),
        ]

        # Variabel kontrol
        self.speed_var   = tk.DoubleVar(value=1.0)
        self.pub_var     = tk.StringVar(value="0")
        self.topic_var   = tk.StringVar(value="temperature")
        self.payload_var = tk.StringVar(value="24.5°C")

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def publish(self):
        """Publish satu pesan dari publisher yang dipilih ke broker."""
        pub_idx = int(self.pub_var.get())
        topic   = self.topic_var.get()
        payload = self.payload_var.get() or "(empty)"
        sp      = self.speed_var.get()
        m       = metrics["ps"]
        color   = TOPIC_COLORS.get(topic, COLOR_PS)
        pub     = self.pubs[pub_idx]

        pub.state         = "active"
        self.broker.state = "idle"

        if not m.tp_start:
            m.tp_start = now()
        m.total += 1
        elapsed = (now() - m.tp_start) / 1000
        m.throughput = m.total / elapsed if elapsed > 0 else 0

        self.log.add("pub", f"📤 {pub.label} → topic:\"{topic}\" payload:\"{payload}\"")
        self._set_status("active", f"{pub.label} publishing \"{topic}\"...")

        def on_broker_arrive():
            pub.state         = "idle"
            self.broker.state = "processing"
            self.log.add("proc", f"⚙ BROKER routing topic:\"{topic}\"...")
            self.canvas.after(int(280 / sp), _route)

        def _route():
            self.broker.state = "active"
            targets = [
                (i, s) for i, s in enumerate(self.subs)
                if topic in SUBSCRIBER_TOPICS.get(s.label, [])
            ]
            self.log.add("proc",
                         f"⚙ BROKER: {len(targets)} subscriber cocok untuk \"{topic}\"")
            if not targets:
                self.log.add("err", f"✗ Tidak ada subscriber untuk topic:\"{topic}\"")
                self.broker.state = "idle"
                self._set_status("idle", "Idle – Sistem Pub-Sub aktif")
                return
            for delay_i, (_, sub) in enumerate(targets):
                self._deliver(sub, topic, color, sp, delay_i * 120)

        self.spawn_packet(
            pub.x, pub.y, self.broker.x, self.broker.y,
            cx=(pub.x + self.broker.x) / 2,
            cy=(pub.y + self.broker.y) / 2 - 20,
            color=color, label=topic[:4],
            speed=0.009 * sp, on_arrive=on_broker_arrive, radius=9,
        )

    def _deliver(self, sub, topic, color, sp, delay_ms):
        """Kirim paket dari broker ke satu subscriber."""
        m = metrics["ps"]

        def send():
            def on_arrive():
                sub.state = "active"
                m.delivered += 1
                self.ptcl.spawn(sub.x, sub.y, color, 7)
                self.log.add("res", f"✓ {sub.label} menerima topic:\"{topic}\"")
                self._update_metrics()
                self._set_status("idle", "Idle – Sistem Pub-Sub aktif")
                self.canvas.after(700, lambda: setattr(sub, "state", "idle"))

            self.spawn_packet(
                self.broker.x, self.broker.y, sub.x, sub.y,
                cx=(self.broker.x + sub.x) / 2,
                cy=(self.broker.y + sub.y) / 2 - 15,
                color=color, label=topic[:4],
                speed=0.008 * sp, on_arrive=on_arrive, radius=8,
            )

        self.canvas.after(delay_ms, send)

    def toggle_auto(self):
        """Toggle mode auto-publish."""
        self.auto_on = not self.auto_on
        if self.auto_on:
            self._auto_loop()
        elif self.auto_id:
            self.canvas.after_cancel(self.auto_id)

    def reset(self):
        """Reset ke kondisi awal."""
        self.packets = []
        for p in self.pubs: p.state = "idle"
        for s in self.subs: s.state = "idle"
        self.broker.state = "idle"
        self.auto_on = False
        reset_metric("ps")
        self._update_metrics()
        self._set_status("idle", "Idle – Sistem Pub-Sub aktif")
        self.log.clear()
        if self.auto_id:
            self.canvas.after_cancel(self.auto_id)
            self.auto_id = None

    # ----------------------------------------------------------------
    # Private
    # ----------------------------------------------------------------

    def _auto_loop(self):
        if not self.auto_on:
            return
        topic = random.choice(list(TOPIC_COLORS))
        vals  = {"temperature": "24.5°C", "pressure": "101.3kPa",
                 "humidity": "65%RH", "alert": "CRITICAL!"}
        self.pub_var.set(str(random.randint(0, 2)))
        self.topic_var.set(topic)
        self.payload_var.set(vals.get(topic, "data"))
        self.publish()
        self.auto_id = self.canvas.after(1800, self._auto_loop)

    def _set_status(self, state, text):
        colors = {"idle": TEXT_3, "active": COLOR_OK,
                  "processing": COLOR_WARN, "error": COLOR_ERR}
        self.lbl["status"].config(text=f"● {text}", fg=colors.get(state, TEXT_2))

    def _update_metrics(self):
        m = metrics["ps"]
        self.lbl["total"].config(text=str(m.total))
        self.lbl["delivered"].config(text=str(m.delivered), fg=COLOR_OK)
        self.lbl["subs"].config(text=str(len(self.subs)))
        self.lbl["tp"].config(text=f"{m.throughput:.2f} msg/s")
        self.lbl["rate"].config(
            text=f"{min(m.delivered / (m.total * 2.5) * 100, 100):.0f}%"
            if m.total else "—")

    # ----------------------------------------------------------------
    # Render
    # ----------------------------------------------------------------

    def render(self, t):
        for p in self.pubs:
            self.draw.draw_connection(p.x, p.y, self.broker.x, self.broker.y,
                                      (p.x + self.broker.x) / 2,
                                      (p.y + self.broker.y) / 2, p.color)
        for s in self.subs:
            self.draw.draw_connection(self.broker.x, self.broker.y, s.x, s.y,
                                      (self.broker.x + s.x) / 2,
                                      (self.broker.y + s.y) / 2, s.color)
        self.draw.draw_text_label(90, 35, "PUBLISHERS", COLOR_RPC, 8, bold=True)
        self.draw.draw_text_label(CANVAS_W - 90, 35, "SUBSCRIBERS", "#80deea", 8, bold=True)
        for p in self.pubs: self.draw.draw_node(p, t)
        self.draw.draw_node(self.broker, t)
        for s in self.subs: self.draw.draw_node(s, t)
        self.draw.draw_text_label(CANVAS_W // 2, 20, "Model: Publish-Subscribe", TEXT_3, 8)
        self.draw.draw_text_label(CANVAS_W // 2, 34, "Pola: Asinkron 1:N", TEXT_3, 8)
