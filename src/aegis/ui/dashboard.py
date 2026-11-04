"""AEGIS v0.3 local MVP dashboard. Run via `streamlit run ...`.

Security: localhost only, non-executing evidence viewer, limited ZIP upload,
no remote AI/cloud calls, raw evidence hidden behind explicit consent toggle.
"""
from __future__ import annotations

import tempfile
import re
from collections import Counter
from pathlib import Path

import streamlit as st

from aegis.detection.engine import assess
from aegis.ingestion.importer import ingest
from aegis.ui import store

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT / 'data' / 'aegis-v1.db'
DEFAULT_RULES = ROOT / 'rules' / 'detection.json'
MAX_ZIP_BYTES = 100 * 1024 * 1024

st.set_page_config(page_title='AEGIS | Offline Assessment', page_icon='🛡️', layout='wide')
st.title('🛡️ AEGIS — Offline Assessment')
st.caption('Milestone 3 • Evidence-based detection • MITRE ATT&CK mapping • Seluruh proses lokal')
st.warning('AEGIS bersifat triase awal. Temuan adalah indikator untuk ditinjau; tidak ada temuan bukan bukti endpoint bersih.', icon='⚠️')

with st.sidebar:
    st.header('Analysis Station')
    st.caption('Beroperasi lokal. Jangan mengekspos dashboard pada jaringan publik.')
    db_path = Path(st.text_input('Lokasi SQLite', value=str(DEFAULT_DB))).expanduser()
    rules_path = Path(st.text_input('Rule pack', value=str(DEFAULT_RULES))).expanduser()
    st.divider()
    st.caption('Import ZIP hanya untuk collection laboratorium tanpa enkripsi. Paket produksi memerlukan perlindungan evidence tambahan.')

if not db_path.is_file():
    st.info('Database belum ditemukan. Gunakan perintah CLI `aegis ingest` terlebih dahulu atau buat database melalui importer CLI.')
    st.stop()

try:
    all_collections = store.collections(db_path)
except (OSError, ValueError) as exc:
    st.error(f'Tidak dapat membuka database: {exc}')
    st.stop()

import_tab, overview_tab, findings_tab, mitre_tab, evidence_tab = st.tabs([
    '📥 Import ZIP', '📊 Overview', '🔎 Findings', '🧭 MITRE ATT&CK', '🗂️ Evidence'
])

with import_tab:
    st.subheader('Import offline collection ZIP')
    last_import = st.session_state.pop('last_import', None)
    if last_import:
        st.success(f"{'ZIP sudah ada' if last_import['duplicate'] else 'ZIP berhasil diimpor'} — Collection #{last_import['collection_id']}, {last_import['rows']} rows")
    st.write('ZIP dibaca langsung oleh AEGIS, tanpa `Server.Utils.ImportCollection`.')
    uploaded = st.file_uploader('Pilih ZIP Velociraptor', type=['zip'], key='collection_zip')
    if uploaded:
        st.caption(f'Ukuran paket: {uploaded.size:,} byte. Batas AEGIS M3: {MAX_ZIP_BYTES // (1024*1024)} MB.')
        if uploaded.size > MAX_ZIP_BYTES:
            st.error('Paket terlalu besar untuk upload dashboard. Gunakan CLI ingest pada filesystem.')
        elif st.button('Validate & import ZIP', type='primary'):
            # Trusted local staging directory, never use original filename as a path.
            incoming = ROOT / 'data' / 'incoming'
            incoming.mkdir(parents=True, exist_ok=True, mode=0o700)
            try:
                # Preserve a safe original basename in collection metadata;
                # never let the uploaded filename control destination directories.
                basename = uploaded.name.replace('\\', '/').split('/')[-1]
                safe_name = re.sub(r'[^A-Za-z0-9._-]', '_', basename)[:128]
                if not safe_name.lower().endswith('.zip') or safe_name in ('.', '..'):
                    safe_name = 'collection-upload.zip'
                with tempfile.TemporaryDirectory(prefix='aegis-', dir=incoming) as tmp_dir:
                    tmp_name = Path(tmp_dir) / safe_name
                    with tmp_name.open('xb') as file:
                        while chunk := uploaded.read(1024 * 1024):
                            file.write(chunk)
                    result = ingest(tmp_name, db_path)
                st.session_state['last_import'] = result
                st.rerun()
            except (OSError, ValueError, RuntimeError) as exc:
                st.error(f'Import gagal: {exc}')

if not all_collections:
    with overview_tab:
        st.info('Belum ada collection. Import ZIP terlebih dahulu.')
    st.stop()

choices = {f"#{x['id']} · {x['filename']} ({x['evidence_count']:,} rows)": x['id'] for x in all_collections}
selected_label = st.selectbox('Collection aktif', list(choices))
collection_id = choices[selected_label]
coll = next(x for x in all_collections if x['id'] == collection_id)

try:
    available_assessments = store.assessments(db_path, collection_id)
    artifact_data = store.artifacts(db_path, collection_id)
    cv = store.profile_coverage(db_path, collection_id)
except (OSError, ValueError) as exc:
    st.error(f'Gagal membaca collection: {exc}')
    st.stop()

with overview_tab:
    st.subheader('Endpoint / Collection Overview')
    a, b, c, d = st.columns(4)
    a.metric('Collection ID', collection_id)
    b.metric('Evidence rows', f"{coll['evidence_count']:,}")
    c.metric('Quick artifacts', f"{len(cv['present'])}/{cv['required']}")
    d.metric('Assessment', len(available_assessments))
    st.caption(f"Imported at (UTC): {coll['imported_at_utc']} | ZIP SHA-256: `{coll['zip_sha256']}`")
    if cv['missing']:
        st.warning('Artifact belum tersedia: ' + ', '.join(cv['missing']))
    else:
        st.info('Semua tipe artifact Quick tersedia. Ini bukan ukuran lengkapnya investigasi.')
    st.dataframe(artifact_data, use_container_width=True, hide_index=True)
    with st.expander('Audit ketersediaan field (bukan persentase deteksi)'):
        audit = store.normalized_field_audit(db_path, collection_id)
        for artifact, details in audit.items():
            st.markdown(f'**{artifact}** — {details["rows_with_any_normalized_value"]}/{details["rows"]} rows memiliki data')
            st.dataframe([{'field': k, 'present': v, 'total': details['rows']} for k, v in details['field_nonempty_rows'].items()],
                         use_container_width=True, hide_index=True)
    st.divider()
    if st.button('Run deterministic assessment', type='primary'):
        try:
            result = assess(db_path, rules_path, collection_id)
            st.success(f"Assessment #{result['assessment_id']} {'digunakan ulang' if result['reused'] else 'dibuat'}: {result['findings_count']} findings")
            st.rerun()
        except (OSError, ValueError, RuntimeError) as exc:
            st.error(f'Assessment gagal: {exc}')

assessment_id = None
assessment_findings = []
if available_assessments:
    latest = available_assessments[0]
    assessment_id = latest['id']
    assessment_findings = store.findings(db_path, assessment_id)

with findings_tab:
    st.subheader('Findings Explorer')
    if not available_assessments:
        st.info('Jalankan assessment pada tab Overview terlebih dahulu.')
    else:
        st.caption(f"Assessment #{assessment_id} • {len(assessment_findings)} raw rule matches • evidence trace tersedia")
        if not assessment_findings:
            st.info('Tidak ada rule match. Ini **tidak** menyimpulkan endpoint aman.')
        else:
            counts = Counter(x['severity'] for x in assessment_findings)
            st.write('Severity:', ' · '.join(f'{k}: {v}' for k, v in sorted(counts.items())))
            shown = [{k: r[k] for k in ('id','severity','rule_id','title','technique_id','source_member','source_row')}
                     for r in assessment_findings]
            st.dataframe(shown, use_container_width=True, hide_index=True)
            st.info('Beberapa rule match dapat berasal dari satu aktivitas aplikasi yang sama. Korelasi bukan atribusi malware.')
            for f in assessment_findings:
                with st.expander(f"#{f['id']} [{f['severity'].upper()}] {f['title']} — {f['rule_id']}"):
                    st.write(f['reason'])
                    st.code(f['observed_value'] or '(tidak tersedia)', language=None)
                    st.caption(f"Evidence ID: {f['evidence_id']} | Source: {f['source_member']} row {f['source_row']}")
                    st.caption(f"MITRE: {f['technique_id'] or 'Unmapped — tidak otomatis teknik ATT&CK'}")

with mitre_tab:
    st.subheader('MITRE ATT&CK Mapping')
    st.caption('Mapping berasal dari rules yang tervalidasi, bukan kesimpulan bebas AI.')
    tagged = [x for x in assessment_findings if x['technique_id']]
    if not tagged:
        st.info('Belum ada temuan yang memiliki mapping MITRE pada assessment ini.')
    else:
        grouped = Counter((x['tactic'], x['technique_id']) for x in tagged)
        matrix = [{'tactic': t or 'unspecified', 'technique': tech, 'finding_count': n}
                  for (t, tech), n in sorted(grouped.items())]
        st.dataframe(matrix, use_container_width=True, hide_index=True)
        st.bar_chart(matrix, x='technique', y='finding_count')
    st.caption('Teknik yang belum terdeteksi tidak berarti tidak pernah digunakan.')

with evidence_tab:
    st.subheader('Evidence Viewer')
    if not assessment_findings:
        st.info('Belum ada findings yang dapat ditelusuri. Gunakan CLI atau Overview untuk membuat assessment.')
    else:
        targets = {f"#{x['id']} — {x['rule_id']} — {x['evidence_id'][:12]}…": x for x in assessment_findings}
        selected = st.selectbox('Pilih finding', list(targets))
        chosen = targets[selected]
        st.caption(f"Source: {chosen['source_member']} row {chosen['source_row']}")
        if st.checkbox('Tampilkan evidence mentah (bisa berisi data pribadi)', value=False):
            item = store.evidence(db_path, chosen['evidence_id'], collection_id)
            if item:
                st.json({'evidence_id': item['evidence_id'], 'source_member': item['source_member'],
                         'source_row': item['source_row'], 'normalized': item['normalized_json'],
                         'raw': item['raw_json']}, expanded=False)
            else:
                st.error('Evidence tidak ditemukan di collection terpilih.')
