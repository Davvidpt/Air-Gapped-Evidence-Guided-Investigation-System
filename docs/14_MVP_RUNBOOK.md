# MVP M1–M4 — runbook dan hasil validasi

Status 8 November 2026: source ingestion, assessment, dashboard, PDF tersedia dan diuji di workspace Debian. AI dan korelasi bukan syarat MVP. Tidak ada perubahan skema SQLite pada M4.

## Mulai dan operasikan

1. Dari root proyek, install `.[mvp,verification]` ke `.venv` sesuai README. Backup database sebelum upgrade source bila menggunakan evidence lab.
2. Jalankan `bash scripts/run_dashboard.sh`. Binding localhost, telemetri mati, upload maksimum 100 MiB.
3. Buka localhost:8501 lewat SSH tunnel bila station tidak memiliki browser.
4. Import ZIP tanpa enkripsi. Database baru dapat dibuat melalui dashboard. Catat collection ID dan SHA-256; pertahankan ZIP master karena staging upload dihapus setelah import.
5. Pilih collection, periksa jumlah artifact dan audit field. Jalankan assessment pada Ringkasan.
6. Tinjau Temuan dan MITRE. Evidence Viewer menampilkan raw JSON hanya setelah checkbox diaktifkan.
7. Pilih assessment aktif di sidebar, buka halaman Laporan, centang label sintetis untuk demo, klik Buat PDF kemudian Unduh PDF. Observed values bersifat opsional dan sensitif. Referensi source member tetap disertakan.
8. Arsipkan laporan dan catat pertanyaan investigasi. Tidak ada rule match tidak berarti aman.

## Ekspor CLI

```bash
PYTHONPATH=src .venv/bin/python -m aegis report \
  --db data/aegis-v1.db --collection 2 --assessment 1 \
  --out reports/AEGIS-collection-2.pdf
```

Assessment harus sudah ada dan milik collection tersebut. Tanpa `--assessment`, pilih assessment terbaru. Database dibuka read-only; isi laporan berasal dari satu transaksi baca. Tidak ada request AI, download MITRE, atau assessment baru saat ekspor.

Output baru berizin 0600. File existing ditolak kecuali `--overwrite`; database input dan symlink dilindungi dari overwrite. PDF berisi status, hash ZIP/ruleset, versi engine, coverage, severity, rule matches, MITRE terkait, evidence ID lengkap, source member/baris, dan batasan. PDF tidak terenkripsi.

## Demo dan validasi otomatis

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/run_mvp_demo.py
```

Script demo selalu membuat direktori baru dan database sintetis terpisah. `--out DIREKTORI_BARU` menentukan lokasi; direktori existing ditolak agar hasil lama tidak tertimpa. `results.json` menyimpan durasi ingest, assessment, PDF dan hasil idempotensi. Waktu fixture kecil tidak merepresentasikan kinerja collection besar.

Hasil yang dibuktikan di workspace:

| Pemeriksaan | Hasil |
|---|---|
| Pengujian M1–M4 dan interaksi UI | 30/30 lulus dengan dependency MVP + verification |
| Baseline sintetis | 5 evidence, 0 matches, NO_RULE_MATCHES |
| Fixture positif | 5 evidence, 4 matches, REVIEW_REQUIRED |
| MITRE fixture positif | T1059.001, T1543.003, T1547.001 |
| Import/assessment berulang | Tidak menggandakan collection atau assessment |
| Dashboard via Streamlit AppTest | Database baru, upload disimulasikan, assessment, raw evidence, PDF download |
| PDF | Header valid, multi-page, source references; observed values hanya saat opt-in |
| Database saat ekspor | Hash file tidak berubah |
| Input tidak tepercaya | Markup di-escape; tidak diperlakukan sebagai link/image PDF |

Verifikasi tambahan pada database lab existing: collection #2 berisi 1.138 evidence dan 2 findings. PDF dibuat di `reports/generated/lab-validation/AEGIS-collection-2.pdf`; hash database sebelum/sesudah ekspor identik. Teks PDF diperiksa terhadap hash ZIP, rule IDs, evidence IDs, dan tidak adanya observed values secara default. File ini bersifat lokal dan diabaikan Git.

AppTest menyimulasikan uploader; ini bukan bukti transfer browser melalui SSH atau penggunaan USB fisik. Pemeriksaan visual PDF sintetis dilakukan pada hasil render halaman pertama.

## Persiapan station offline

Di mesin staging dengan versi Python, OS, dan arsitektur yang sesuai station:

```bash
.venv/bin/python -m pip wheel --wheel-dir wheelhouse '.[mvp,verification]'
```

Pindahkan wheelhouse dan source melalui media tepercaya. Di station:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --no-index --find-links wheelhouse 'aegis-offline[mvp,verification]'
```

Simpan manifest hash serta versi wheel yang dipakai untuk deployment. Ulangi demo dengan jaringan VM dimatikan sebagai acceptance operasional. Kode analisis dan report tidak membutuhkan layanan internet; pengujian pemutusan jaringan VM secara fisik belum dibuktikan oleh suite.

## Acceptance operator

- [x] Koleksi Windows baru menggunakan USB — dilaporkan selesai oleh pengguna pada 8 November 2026.
- [x] Upload dan unduh PDF melalui browser via SSH tunnel — dilaporkan selesai oleh pengguna pada 8 November 2026, sebelum pembaruan tampilan.
- [ ] Cek ulang navigasi dan unduh PDF melalui browser setelah pembaruan tampilan.
- [ ] Bandingkan source row pada PDF dengan ZIP master dan dashboard.
- [ ] Jalankan workflow saat jaringan VM dimatikan setelah dependency siap.
- [ ] Rekam demo, finalisasi slide/video dan audit repository sebelum submission.

MVP software dapat diuji lokal. Acceptance perangkat fisik, video, dan submission tidak boleh dianggap selesai hanya dari unit tests.

Referensi implementasi PDF: [ReportLab Platypus](https://docs.reportlab.com/reportlab/userguide/ch5_platypus/).

## Pembaruan tampilan dashboard

Menggunakan `streamlit-antd-components==0.3.2` (MIT) untuk menu Ant Design pada sidebar, dengan icon Ant Design yang dibundel. Tema terang navy/teal dan CSS berada di `src/aegis/ui/theme.py`; font menggunakan font sistem. Tidak ada stylesheet atau font dari CDN yang ditambahkan. Minimum Streamlit dinaikkan ke 1.49 untuk parameter lebar tabel yang baru.

Halaman: Ringkasan, Impor ZIP, Temuan, MITRE ATT&CK, Evidence, Laporan. Collection dan assessment aktif dipilih di sidebar; halaman Temuan memiliki filter severity dan pencarian. Laporan yang telah dibuat tetap dapat diunduh selama konteks dan opsi tidak berubah.

Verifikasi: 30 tes lulus, mencakup serialisasi menu komunitas, rute halaman, filter dan empty states, impor database baru, assessment berulang, evidence dan unduh PDF. Klik menu iframe disimulasikan pada AppTest. Pemeriksaan visual Chromium belum berhasil karena library sistem browser tidak tersedia; layout desktop/mobile dan request browser saat offline belum diverifikasi secara langsung.
