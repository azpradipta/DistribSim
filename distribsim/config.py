"""
distribsim/config.py
Konstanta warna, ukuran canvas, dan konfigurasi global.
"""

# ================================================================
# Warna Tema (Dark Mode)
# ================================================================

BG_ROOT   = "#07080f"   # Latar belakang utama
BG_PANEL  = "#0d0f1c"   # Panel kontrol
BG_DARK   = "#060710"   # Canvas dan area gelap
BG_CARD   = "#111326"   # Card / widget kotak
BORDER    = "#1e2235"   # Warna garis border

TEXT_1    = "#e8eaf6"   # Teks utama (terang)
TEXT_2    = "#8890b5"   # Teks sekunder
TEXT_3    = "#454870"   # Teks tersier / label kecil

# Warna per model komunikasi
COLOR_RR  = "#4fc3f7"   # Request-Response : Cyan
COLOR_PS  = "#ce93d8"   # Publish-Subscribe : Ungu
COLOR_RPC = "#a5d6a7"   # Remote Procedure Call : Hijau
COLOR_ACC = "#ffb74d"   # Aksen / Server

# Warna status
COLOR_OK   = "#66bb6a"  # Sukses
COLOR_ERR  = "#ef5350"  # Error / Gagal
COLOR_WARN = "#ffd54f"  # Peringatan / Processing

# ================================================================
# Ukuran Canvas Simulasi
# ================================================================

CANVAS_W = 780   # Lebar canvas animasi (pixels)
CANVAS_H = 420   # Tinggi canvas animasi (pixels)
