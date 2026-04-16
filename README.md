# ⬡ DistribSim

**Simulasi Interaktif Model Komunikasi Sistem Terdistribusi**

> Tugas 2 — Mata Kuliah Sistem Paralel & Terdistribusi

DistribSim adalah aplikasi desktop berbasis Python/Tkinter yang memvisualisasikan tiga model komunikasi utama dalam sistem terdistribusi secara interaktif dan real-time: **Request-Response**, **Publish-Subscribe**, dan **Remote Procedure Call (RPC)**.

---

## 📸 Tampilan Aplikasi

| Tab | Deskripsi |
|-----|-----------|
| ⇄ Request-Response | Animasi aliran HTTP request/response antara Client dan Server |
| ◎ Publish-Subscribe | Visualisasi routing pesan dari Publisher → Broker → Subscriber |
| ⟳ Remote Procedure Call | Simulasi 8 langkah eksekusi RPC melalui stub/skeleton |
| ≡ Perbandingan | Tabel & kartu metrik real-time ketiga model secara berdampingan |

---

## ✨ Fitur Utama

- 🎬 **Animasi 60fps** — paket data bergerak mengikuti kurva Bézier dengan efek trail
- 💥 **Efek partikel** — burst effect saat paket tiba di node tujuan
- 📊 **Metrik real-time** — total request, latensi rata-rata, throughput, success rate
- ⚙️ **Kontrol interaktif** — slider kecepatan animasi, latensi server, mode otomatis
- 🔴 **Simulasi kegagalan** — mode error/timeout dengan probabilitas yang dapat dikonfigurasi
- 🌙 **Dark theme** — antarmuka gelap modern dengan palet warna per model
- 📋 **Log komunikasi** — histori pesan real-time dengan kode warna per jenis event

---

## 🏗️ Struktur Proyek

```
tugas2sister/
│
├── main.py                        # Entry point aplikasi
│
└── distribsim/                    # Package utama
    │
    ├── __init__.py
    ├── config.py                  # Konstanta warna, ukuran canvas, tema
    ├── data_models.py             # NodeDef, Packet, Metric (dataclasses)
    ├── base_sim.py                # BaseSimulation — animation loop 60fps
    ├── draw_engine.py             # DrawEngine + ParticleSystem
    ├── utils.py                   # Bezier, blend_color, fmt_ms, dll.
    │
    ├── models/                    # Logika simulasi per model
    │   ├── __init__.py
    │   ├── sim_rr.py              # RequestResponseSim
    │   ├── sim_ps.py              # PubSubSim
    │   └── sim_rpc.py             # RPCSim
    │
    └── ui/                        # Komponen antarmuka pengguna
        ├── __init__.py
        ├── app.py                 # DistribSimApp — window & tab builder
        ├── comparison.py          # ComparisonTab — tabel & kartu perbandingan
        └── widgets.py             # LogWidget, styled_button, build_metric_grid, dll.
```

---

## 🔬 Model Komunikasi yang Disimulasikan

### 1. ⇄ Request-Response (HTTP/REST)

**Pola:** Sinkron, Point-to-Point (1:1)

Client mengirim request dan **memblokir** operasi hingga menerima respons dari server. Mensimulasikan alur HTTP lengkap termasuk pemrosesan server dan kemungkinan kegagalan.

```
CLIENT ──[HTTP GET/POST/PUT/DELETE]──▶ SERVER
CLIENT ◀──────────[200 OK / 500 Error]────── SERVER
```

**Fitur simulasi:**
- Pilihan metode HTTP: GET, POST, PUT, DELETE
- Slider latensi server: 100ms — 3000ms
- Probabilitas kegagalan 30% (opsional)
- Mode pengiriman otomatis

---

### 2. ◎ Publish-Subscribe (MQTT/Kafka)

**Pola:** Asinkron, One-to-Many (1:N)

Publisher tidak mengetahui siapa subscriber-nya — pengiriman dilakukan melalui **Broker** berdasarkan topic. Publisher dan subscriber terdekopel penuh (loose coupling).

```
PUB-1 (Sensor Suhu)       ──▶ ┌─────────┐ ──▶ SUB-A (Dashboard)
PUB-2 (Sensor Tekanan)    ──▶ │  BROKER │ ──▶ SUB-B (Alert Sys)
PUB-3 (Sensor Kelembaban) ──▶ └─────────┘ ──▶ SUB-C (Logger)
                                            ──▶ SUB-D (Actuator)
```

**Subscription Matrix:**

| Subscriber | temperature | pressure | humidity | alert |
|------------|:-----------:|:--------:|:--------:|:-----:|
| SUB-A (Dashboard) | ✓ | ✓ | ✓ | ✓ |
| SUB-B (Alert Sys) | — | — | — | ✓ |
| SUB-C (Logger)    | ✓ | ✓ | ✓ | ✓ |
| SUB-D (Actuator)  | ✓ | — | ✓ | — |

**Fitur simulasi:**
- 3 publisher, 4 subscriber, 4 topic
- Routing otomatis berdasarkan subscription matrix
- Mode auto-publish dengan interval acak
- Custom payload per pesan

---

### 3. ⟳ Remote Procedure Call (gRPC/CORBA)

**Pola:** Sinkron-Transparan, Prosedural (1:1)

Client memanggil fungsi remote **seolah-olah fungsi lokal**. Proses marshaling/unmarshaling parameter disembunyikan oleh stub dan skeleton.

```
CLIENT → C-STUB → NETWORK → S-SKEL → SERVER
                                         ↓ eksekusi
CLIENT ← C-STUB ← NETWORK ← S-SKEL ← SERVER
```

**8 Langkah Eksekusi RPC:**

1. Client memanggil fungsi lokal (stub)
2. Stub: marshaling parameter → format jaringan
3. Transmisi via TCP/HTTP2
4. Skeleton: menerima & unmarshal
5. Server mengeksekusi prosedur
6. Hasil di-marshal & dikirim balik
7. Transmisi respons via jaringan
8. Client menerima hasil akhir

**Fungsi RPC tersedia:**
- `getUser(userId=42)` → `{ id:42, name:"Ahmad Fariz" }`
- `calculateSum(a=10, b=20)` → `30`
- `getWeather("Jakarta")` → `{ temp:32°C, humid:80% }`
- `processOrder(orderId=101)` → `{ status:"confirmed" }`

---

## 📊 Perbandingan Model

| Karakteristik | Request-Response | Publish-Subscribe | RPC |
|---------------|:----------------:|:-----------------:|:---:|
| Pola Komunikasi | Sinkron (1:1) | Asinkron (1:N) | Sinkron (1:1) |
| Coupling | 🔴 Tinggi | 🟢 Rendah | 🔴 Tinggi |
| Skalabilitas | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Fault Tolerance | Manual retry | Built-in (queue) | Retry + timeout |
| Overhead Jaringan | Rendah | Sedang (broker) | Sedang (marshal) |
| Use Case | REST API, CRUD | IoT, Events, Streaming | Microservices, gRPC |
| Contoh Protokol | HTTP, WebSocket | MQTT, AMQP, Kafka | gRPC, XML-RPC |

---

## 🚀 Cara Menjalankan

### Prasyarat

- Python **3.8** atau lebih baru
- Tkinter (sudah built-in bersama Python — tidak perlu install terpisah)

### Langkah

```bash
# 1. Clone repository
git clone https://github.com/<username>/tugas2sister.git
cd tugas2sister

# 2. Jalankan aplikasi
python main.py
```

> **Catatan Windows:** Jika Python diinstall dari Microsoft Store, Tkinter mungkin perlu diinstall terpisah. Disarankan menggunakan installer resmi dari [python.org](https://www.python.org/downloads/).

---

## 🧩 Arsitektur Kode

### Inheritance Simulasi

```
BaseSimulation          (distribsim/base_sim.py)
├── RequestResponseSim  (distribsim/models/sim_rr.py)
├── PubSubSim           (distribsim/models/sim_ps.py)
└── RPCSim              (distribsim/models/sim_rpc.py)
```

`BaseSimulation` menyediakan:
- Loop animasi `canvas.after(16ms)` ≈ 60fps
- Update posisi paket via kurva Bézier kuadratik
- Sistem spawn paket dengan callback `on_arrive`
- Integrasi `DrawEngine` dan `ParticleSystem`

### Alur Data Global

```
distribsim/data_models.py
  └── metrics: dict{"rr": Metric, "ps": Metric, "rpc": Metric}
        ↑                                   ↑
    sim_rr/ps/rpc.py              comparison.py (dibaca tiap 2 detik)
```

### Rendering Pipeline (per frame)

```
_tick()
  ├── draw.clear()           # Bersihkan canvas
  ├── draw.draw_bg()         # Background dot-grid
  ├── _update_packets()      # Majukan posisi paket + draw trail
  ├── render(t)              # Draw node, koneksi, label (subclass)
  └── ptcl.update_draw()     # Render partikel di layer teratas
```

---

## 🎨 Desain & Tema

### Palet Warna

| Token | Hex | Penggunaan |
|-------|-----|-----------|
| `COLOR_RR` | `#4fc3f7` | Request-Response (Cyan) |
| `COLOR_PS` | `#ce93d8` | Publish-Subscribe (Ungu) |
| `COLOR_RPC` | `#a5d6a7` | Remote Procedure Call (Hijau) |
| `COLOR_OK` | `#66bb6a` | Status sukses |
| `COLOR_ERR` | `#ef5350` | Status error/gagal |
| `COLOR_WARN` | `#ffd54f` | Status processing/peringatan |
| `BG_ROOT` | `#07080f` | Background utama |
| `BG_DARK` | `#060710` | Canvas area |

### Efek Visual
- **Glow effect** — node aktif memancarkan cahaya berlapis
- **Pulse animation** — node berdetak saat memproses
- **Bézier trail** — jejak paket memudar mengikuti kurva
- **Particle burst** — ledakan partikel saat paket tiba
- **State badge** — ikon ●/⟳/✗ di pojok node sesuai state

---

## 📁 Detail Modul

### `distribsim/config.py`
Seluruh konstanta aplikasi: warna tema, ukuran canvas (`780×420px`), dan token tipografi.

### `distribsim/data_models.py`
Tiga dataclass inti:
- `NodeDef` — posisi, label, warna, dan state sebuah node
- `Packet` — paket bergerak dengan kurva Bézier dan callback `on_arrive`
- `Metric` — akumulasi statistik (total, success, latencies, throughput)

### `distribsim/draw_engine.py`
- `DrawEngine` — semua operasi drawing: background, node, koneksi, paket, label
- `ParticleSystem` — sistem partikel dengan gravitasi dan fade-out

### `distribsim/utils.py`
Fungsi utilitas murni: `bezier()`, `blend_color()`, `fmt_ms()`, `now()`, `lerp()`, `clamp()`

### `distribsim/ui/widgets.py`
Factory function widget bertema dark:
- `LogWidget` — area log berwarna dengan tag per jenis event
- `styled_button()` — tombol dengan glow effect
- `styled_scale()` — slider
- `styled_combo()` — dropdown
- `build_metric_grid()` — panel metrik real-time

---

## 👤 Informasi Tugas

| | |
|--|--|
| **Mata Kuliah** | Sistem Paralel dan Terdistribusi |
| **Tugas** | Tugas 2 — Simulasi Model Komunikasi |
| **Teknologi** | Python 3.x, Tkinter |
| **Platform** | Windows / Linux / macOS |

---

## 📄 Lisensi

Proyek ini dibuat untuk keperluan akademis. Silakan digunakan sebagai referensi pembelajaran.
