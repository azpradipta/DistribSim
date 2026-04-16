"""
distribsim/data_models.py
Data models (dataclass) dan global state bersama semua modul simulasi.

Berisi:
- NodeDef    : Representasi node dalam sistem terdistribusi
- Packet     : Paket/pesan yang bergerak antar node di canvas
- Metric     : Struktur data metrik simulasi
- metrics    : Global state metrik untuk setiap model
- reset_metric() : Helper untuk mereset satu metrik
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, List


# ================================================================
# DATA CLASSES
# ================================================================

@dataclass
class NodeDef:
    """
    Mendefinisikan satu node dalam sistem terdistribusi.
    Ditampilkan sebagai lingkaran animasi di canvas.
    """
    x: float           # Posisi horizontal di canvas
    y: float           # Posisi vertikal di canvas
    label: str         # Nama node (teks di dalam lingkaran)
    sublabel: str      # Peran node (teks di bawah lingkaran)
    color: str         # Warna node (hex string)
    radius: float = 36
    state: str = "idle"   # "idle" | "active" | "processing" | "error"


@dataclass
class Packet:
    """
    Representasi paket/pesan bergerak antar node.
    Bergerak mengikuti kurva bezier dari source ke destination.
    """
    sx: float; sy: float           # Koordinat sumber
    dx: float; dy: float           # Koordinat tujuan
    cx: float; cy: float           # Control point kurva bezier
    t: float = 0.0                 # Progress perjalanan [0.0 .. 1.0]
    speed: float = 0.01            # Kecepatan per frame
    color: str = "#4fc3f7"
    label: str = ""
    done: bool = False
    on_arrive: Optional[Callable] = None   # Callback saat paket tiba
    radius: float = 10


@dataclass
class Metric:
    """Metrik simulasi untuk satu model komunikasi."""
    total: int = 0
    success: int = 0
    fail: int = 0
    latencies: list = field(default_factory=list)
    throughput: float = 0.0
    tp_start: float = 0.0
    tp_count: int = 0
    delivered: int = 0   # Khusus Pub-Sub: jumlah pesan terkirim ke subscriber


# ================================================================
# GLOBAL STATE
# ================================================================

metrics: dict = {
    "rr":  Metric(),   # Request-Response
    "ps":  Metric(),   # Publish-Subscribe
    "rpc": Metric(),   # Remote Procedure Call
}


def reset_metric(key: str):
    """Reset metrik satu model ke kondisi awal."""
    metrics[key] = Metric()
