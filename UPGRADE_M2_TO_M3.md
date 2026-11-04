# Upgrade M2 → M3 (non-destructive)

Patch M3 menambah dashboard Streamlit dan query backend tanpa memodifikasi file M1/M2 yang ada dan **tanpa migrasi database**.

1. Masuk ke folder proyek: `cd ~/AEGIS_M1`.
2. Backup: `cp -p data/aegis-v1.db data/aegis-v1.db.before-m3`.
3. Extract patch dalam folder proyek: `unzip -o ~/AEGIS_M3_Patch.zip -d .`.
4. Jalankan: `PYTHONPATH=src python3 -m unittest discover -s tests -v` (target 21 tests).
5. Baca panduan: `cat docs/13_M3_DASHBOARD.md`.
6. Buat `.venv`, install Streamlit, dan buka dashboard melalui SSH tunnel.

Jangan extract patch dari `~` dengan `-d .`; file akan tercecer di luar proyek.
