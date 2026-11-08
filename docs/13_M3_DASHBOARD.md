# M3 — Dashboard AEGIS lokal

## Scope

- Import ZIP Velociraptor v0.77.3 **tanpa enkripsi** langsung ke SQLite, tanpa `ImportCollection`.
- Memilih collection lama (termasuk ID 2), melihat 4 artifact/field coverage, menjalankan rules M2.
- Melihat findings dengan tautan evidence ID, ringkasan mapping ATT&CK, dan detail evidence (atas pilihan operator).
- M4 menambahkan halaman Laporan PDF; lihat `14_MVP_RUNBOOK.md`. **Belum** menyediakan AI, MITRE Enterprise matrix lengkap, automatic benign/malicious classification, akun login, atau korelasi multi-endpoint.

## Instalasi di Debian (satu kali ketika internet tersedia)

```bash
cd ~/AEGIS_M1
python3 -m venv .venv
. .venv/bin/activate
python -m pip install '.[mvp]'
```

Untuk penggunaan berikutnya, tidak perlu koneksi internet selama paket Python sudah terpasang. Streamlit digunakan lokal, jangan deploy ke jaringan terbuka tanpa autentikasi dan hardening.

## Jalankan

```bash
cd ~/AEGIS_M1
. .venv/bin/activate
PYTHONPATH=src python -m streamlit run src/aegis/ui/dashboard.py \
  --server.address 127.0.0.1 --server.port 8501 \
  --server.maxUploadSize 100 --server.headless true
```

Jika Debian VM tanpa desktop, pada Windows host buka PowerShell:

```powershell
ssh -N -L 8501:127.0.0.1:8501 srv-admin@IP_LINUX_VM
```

Kemudian di Windows host buka `http://127.0.0.1:8501`.

## Tes sebelum demo

```bash
cd ~/AEGIS_M1
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m aegis summary --db data/aegis-v1.db --collection 2
```

Dalam Ringkasan, pilih collection #2, harus muncul 1.138 evidence rows, empat jenis artifact, dan setidaknya satu assessment jika M2 sudah pernah dijalankan. Temuan dari direktori temporary tetap berstatus indikator heuristik; nama program saja tidak cukup untuk pengecualian/simpulan.

## Keamanan

- File ZIP dan hasil parsed dapat berisi data sensitif. Batasi akses Debian VM dan batasi hak akses ke `data/`.
- Streamlit hanya di-bind ke `127.0.0.1`, akses host lain hanya dengan SSH tunnel.
- Upload UI dibatasi 100 MB, ZIP divalidasi oleh importer M1, disimpan sementara di folder internal acak lalu dibersihkan. Arsip tidak diekstrak ke filesystem.
- Hasil mentah tersembunyi secara default; aktifkan secara sadar untuk investigasi.
- Tidak mengubah skema SQLite; backup database sebelum upgrade. Importer dan assessor tetap menulis SQLite ketika operator mengklik tombol eksplisit.
- ZIP asli harus disimpan terpisah sebagai evidence master; `ZIP SHA-256` dalam database hanyalah hash yang dihitung saat impor, bukan tanda tangan digital dari collector.

## Keterbatasan

- Dashboard belum dilengkapi autentikasi atau audit operator; jangan mengekspos port 8501 publik.
- `Quick coverage 4/4` hanyalah keberadaan artifact, bukan kemampuan deteksi atau tingkat keamanan sistem.
- MITRE mapping tidak muncul untuk `AEGIS-PROCESS-001` karena hanya anomali lokasi tanpa teknik spesifik.
- Dua temuan dari proses yang berhubungan tetap tampil sebagai dua rule matches; deduplikasi berbasis korelasi membutuhkan proses pengembangan berikutnya.

## Pembaruan MVP M4

Dashboard mendukung database baru dari upload pertama dan halaman Laporan PDF dengan pilihan assessment pada sidebar. Gunakan `bash scripts/run_dashboard.sh` untuk binding localhost dan menonaktifkan telemetri. Pengujian interaksi ada di `tests/test_mvp_ui.py`.

## Navigasi Ant Design

Pembaruan tampilan memakai `streamlit-antd-components==0.3.2` (MIT). Sidebar berisi Ringkasan, Impor ZIP, Temuan, MITRE ATT&CK, Evidence dan Laporan. Collection serta assessment aktif berlaku di seluruh halaman. Path SQLite/rules berada pada expander Pengaturan station. Tema dan aset komponen dipasang lokal; siapkan dependency ini juga dalam wheelhouse offline. Lihat runbook untuk status pengujian browser.
