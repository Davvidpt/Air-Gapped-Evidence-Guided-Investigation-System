# AEGIS — Air-Gapped Evidence & Guided Investigation System

**v0.4.1 — MVP laboratorium M1–M4:** ingestion ZIP, evidence SQLite, assessment deterministik, mapping ATT&CK terbatas, dashboard lokal, dan laporan PDF berbahasa Indonesia. AI lokal dan korelasi antar-endpoint masih direncanakan.

AEGIS membantu triase Windows di lingkungan offline. Velociraptor mengumpulkan artifact; AEGIS mengolah ZIP langsung tanpa `Server.Utils.ImportCollection`. Temuan adalah indikator untuk ditinjau, bukan vonis infeksi. **Tidak ada rule match tidak membuktikan endpoint bersih.**

`USB collector → ZIP → validasi + normalisasi → SQLite → rules → findings + evidence IDs → dashboard / PDF`

## Instalasi

Python 3.10+ di Linux. Jalankan dari root proyek. Ingestion/assessment menggunakan standard library; dashboard dan PDF memerlukan dependency tambahan.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install '.[mvp,verification]'
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Dependency `verification` hanya untuk pemeriksaan PDF. Setup membutuhkan internet atau wheelhouse yang disiapkan sebelumnya; analisis berikutnya berjalan lokal. Lihat [panduan MVP](docs/14_MVP_RUNBOOK.md) untuk persiapan offline.

## Jalankan dashboard

```bash
bash scripts/run_dashboard.sh
```

Buka `http://127.0.0.1:8501`. Dari Windows host, gunakan SSH tunnel:

```powershell
ssh -N -L 8501:127.0.0.1:8501 srv-admin@IP_LINUX_VM
```

Dashboard dapat menerima impor pertama tanpa database sebelumnya. Navigasi menggunakan sidebar Ant Design: **Impor ZIP → pilih collection → Ringkasan: Jalankan assessment → Temuan / MITRE / Evidence → Laporan: Buat PDF → Unduh PDF**. Pilih collection dan assessment aktif pada sidebar; pengaturan path tersedia di Pengaturan station. Upload dibatasi 100 MiB. Dashboard tidak memiliki autentikasi; gunakan localhost dan SSH tunnel. Telemetri Streamlit dinonaktifkan melalui konfigurasi proyek.

Tampilan menggunakan [Streamlit Ant Design Components](https://github.com/nicedouble/StreamlitAntdComponents) (MIT), tema terang navy/teal, filter temuan, dan halaman terpisah. Dependency komponen sudah termasuk extra `mvp`; aset komponennya dibundel lokal.

## Demo sintetis lengkap

```bash
.venv/bin/python scripts/run_mvp_demo.py
```

Script membuat direktori baru di `reports/generated/` berisi dua ZIP sintetis, dua database terpisah, PDF berlabel sintetis, dan `results.json` dengan durasi serta pemeriksaan idempotensi. Baseline: **0 matches**. Fixture positif: **4 matches, 3 teknik MITRE**. Ini pengujian fungsi, bukan pengukuran akurasi malware.

## CLI untuk evidence lab

```bash
PYTHONPATH=src .venv/bin/python -m aegis ingest PATH_COLLECTION.zip --db data/aegis-v1.db
PYTHONPATH=src .venv/bin/python -m aegis inspect-fields --db data/aegis-v1.db --collection 2
PYTHONPATH=src .venv/bin/python -m aegis assess --db data/aegis-v1.db --collection 2
PYTHONPATH=src .venv/bin/python -m aegis report --db data/aegis-v1.db --collection 2 --out reports/AEGIS-collection-2.pdf
```

Gunakan ID dari hasil ingest. Collection yang sudah diimpor tidak perlu diimpor ulang. Report memakai assessment terbaru pada collection tersebut; `--assessment ID` memilih assessment tertentu. Ekspor membaca database tanpa migrasi atau analisis ulang. File keluaran yang sudah ada ditolak kecuali `--overwrite`; observed values tidak disertakan kecuali `--include-observed`. Tambahkan `--synthetic` untuk data demonstrasi.

## Batas MVP dan dokumentasi

Empat artifact Quick: Pslist, Netstat, Services, StartupItems. Empat rules heuristik dan tiga ID ATT&CK lokal; bukan dataset Enterprise penuh. Coverage 4/4 hanya keberadaan artifact, bukan kelengkapan field atau persentase keamanan. ZIP terenkripsi, AI, korelasi lintas-endpoint dan autentikasi belum tersedia. Simpan ZIP master terpisah; hash saat diterima tidak membuktikan keaslian historis.

- [Catatan rilis](CHANGELOG.md)
- [Panduan MVP dan validasi](docs/14_MVP_RUNBOOK.md)
- [Arsitektur](docs/01_ARCHITECTURE.md)
- [Kontrak data](docs/02_DATA_CONTRACT.md)
- [Rules dan M2](docs/12_M2_IMPLEMENTATION.md)
- [Dashboard](docs/13_M3_DASHBOARD.md)
- [SOP operator](docs/06_OPERATOR_SOP.md)
- [Batasan](docs/10_LIMITATIONS.md)

Jangan commit evidence ZIP, SQLite, laporan sensitif, atau model weights. Dokumen handover 8 November merupakan catatan historis; status implementasi terbaru ada pada README dan runbook MVP.
