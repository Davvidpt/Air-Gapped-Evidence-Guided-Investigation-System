# Catatan rilis

## 0.4.1 — 8 November 2026

- Melengkapi MVP M1–M4: dashboard lokal dengan navigasi Ant Design, filter temuan, pemilihan collection dan assessment, serta ekspor PDF berbahasa Indonesia.
- Menambahkan CLI `aegis report`, demo sintetis lengkap, konfigurasi Streamlit localhost, dan skrip menjalankan dashboard.
- Memperbarui README, kontrak data, SOP operator, serta panduan dashboard dan [runbook MVP](docs/14_MVP_RUNBOOK.md).
- Menambahkan pengujian laporan PDF dan interaksi dashboard.
- Mengabaikan dokumentasi progress lokal (`AEGIS_Dokumentasi_*`), arsip patch (`AEGIS_*_Patch*`), dan collection endpoint (`Collection-*` / `collection-*`) melalui `.gitignore`. Arsip ZIP dan database tetap diabaikan.

Versi package dan `aegis.__version__` diselaraskan ke `0.4.1`. Skema SQLite tidak berubah pada pembaruan M4; cadangkan database sebelum memperbarui instalasi. Batasan dan acceptance operator yang belum selesai dicatat dalam runbook MVP.
