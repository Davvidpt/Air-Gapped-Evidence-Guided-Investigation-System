"""Local AEGIS workspace with community Ant Design navigation."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import sqlite3
import tempfile

import streamlit as st
import streamlit_antd_components as sac

from aegis.detection.engine import assess
from aegis.ingestion.importer import ingest
from aegis.ui import store
from aegis.ui.theme import apply_theme, brand

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB = ROOT / 'data/aegis-v1.db'
DEFAULT_RULES = ROOT / 'rules/detection.json'
MAX_ZIP_BYTES = 100 * 1024 * 1024
PAGES = {
    'Ringkasan': ('Ringkasan investigasi', 'Pantau evidence, cakupan koleksi, dan hasil assessment dalam satu ruang kerja.'),
    'Impor ZIP': ('Impor koleksi baru', 'Masukkan hasil Velociraptor Offline Collector untuk memulai pemeriksaan.'),
    'Temuan': ('Jelajahi temuan', 'Tinjau indikator, alasan rule, dan referensi evidence yang mendasarinya.'),
    'MITRE ATT&CK': ('Pemetaan MITRE ATT&CK', 'Lihat asosiasi teknik dari rules yang cocok dengan evidence.'),
    'Evidence': ('Telusuri evidence', 'Periksa sumber temuan dan buka data mentah saat diperlukan.'),
    'Laporan': ('Laporan investigasi', 'Ekspor assessment tersimpan menjadi laporan PDF yang dapat ditelusuri.'),
}
ERRORS = (OSError, ValueError, RuntimeError, sqlite3.Error)

st.set_page_config(page_title='AEGIS | Ruang Investigasi', page_icon='🛡️', layout='wide')
apply_theme()

with st.sidebar:
    brand()
    st.markdown('<span class="aegis-status">● STATION LOKAL</span>', unsafe_allow_html=True)
    st.divider()
    with st.expander('Pengaturan station', expanded=False):
        db_path = Path(st.text_input('Lokasi SQLite', value=str(DEFAULT_DB))).expanduser()
        rules_path = Path(st.text_input('Rule pack', value=str(DEFAULT_RULES))).expanduser()
        st.caption('Akses melalui localhost atau SSH tunnel.')

try:
    all_collections = store.collections(db_path) if db_path.is_file() else []
except ERRORS as exc:
    st.error(f'Tidak dapat membuka database: {exc}')
    st.stop()

with st.sidebar:
    st.markdown('<div class="aegis-eyebrow">Ruang kerja</div>', unsafe_allow_html=True)
    page = sac.menu([
        sac.MenuItem('Ringkasan', icon=sac.AntIcon('DashboardOutlined')),
        sac.MenuItem('Impor ZIP', icon=sac.AntIcon('InboxOutlined')),
        sac.MenuItem('Temuan', icon=sac.AntIcon('SearchOutlined')),
        sac.MenuItem('MITRE ATT&CK', icon=sac.AntIcon('ApartmentOutlined')),
        sac.MenuItem('Evidence', icon=sac.AntIcon('DatabaseOutlined')),
        sac.MenuItem('Laporan', icon=sac.AntIcon('FileTextOutlined')),
    ], index=0 if all_collections else 1, size='md', color='teal',
       variant='light', key='workspace_navigation')
    st.divider()
    coll = None
    available_assessments = []
    assessment_id = None
    if all_collections:
        st.markdown('<div class="aegis-eyebrow">Konteks investigasi</div>', unsafe_allow_html=True)
        by_id = {c['id']: c for c in all_collections}
        pending = st.session_state.pop('pending_collection', None)
        if pending and pending[0] == str(db_path) and pending[1] in by_id:
            st.session_state[f'collection:{db_path}'] = pending[1]
        collection_id = st.selectbox('Collection aktif', list(by_id),
                                    format_func=lambda cid: f"#{cid} · {by_id[cid]['filename']}",
                                    key=f'collection:{db_path}')
        coll = by_id[collection_id]
        try:
            available_assessments = store.assessments(db_path, collection_id)
        except ERRORS as exc:
            st.error(f'Gagal membaca assessment: {exc}')
            st.stop()
        if available_assessments:
            pending = st.session_state.pop('pending_assessment', None)
            if pending and pending[:2] == (str(db_path), collection_id):
                st.session_state[f'assessment:{db_path}:{collection_id}'] = pending[2]
            assessment_id = st.selectbox('Assessment aktif', [a['id'] for a in available_assessments],
                                         format_func=lambda aid: f'Assessment #{aid}',
                                         key=f'assessment:{db_path}:{collection_id}')
        else:
            st.caption('Assessment belum dijalankan.')
    st.divider()
    st.caption('AEGIS · MVP M1–M4')
    st.caption('Triase offline dengan referensi evidence. Temuan memerlukan tinjauan operator.')

page = page if page in PAGES else 'Ringkasan'
st.caption(f'RUANG INVESTIGASI  /  {page.upper()}')
st.title(PAGES[page][0])
st.caption(PAGES[page][1])

last_import = st.session_state.pop('last_import', None)
if last_import:
    st.success(f"{'ZIP sudah ada' if last_import['duplicate'] else 'ZIP berhasil diimpor'} — Collection #{last_import['collection_id']}, {last_import['rows']:,} evidence rows")
last_assessment = st.session_state.pop('last_assessment', None)
if last_assessment:
    st.success(last_assessment)

if page == 'Impor ZIP':
    left, right = st.columns([2, 1], gap='large')
    with left, st.container(border=True, key="panel_import"):
        st.subheader('Tambahkan paket evidence')
        st.write('Pilih ZIP hasil collector Windows. AEGIS memvalidasi paket sebelum menyimpan evidence.')
        uploaded = st.file_uploader('Pilih ZIP Velociraptor', type=['zip'], key='collection_zip')
        if uploaded:
            st.caption(f'Ukuran paket: {uploaded.size:,} byte · maksimum 100 MiB')
            if uploaded.size > MAX_ZIP_BYTES:
                st.error('Paket terlalu besar. Gunakan CLI ingest untuk paket di filesystem.')
            elif st.button('Validasi & impor ZIP', type='primary'):
                incoming = ROOT / 'data' / 'incoming'
                try:
                    incoming.mkdir(parents=True, exist_ok=True, mode=0o700)
                    basename = uploaded.name.replace('\\', '/').split('/')[-1]
                    safe_name = re.sub(r'[^A-Za-z0-9._-]', '_', basename)[:128]
                    if not safe_name.lower().endswith('.zip') or safe_name in ('.', '..'):
                        safe_name = 'collection-upload.zip'
                    with st.spinner('Memvalidasi dan mengimpor evidence...'):
                        with tempfile.TemporaryDirectory(prefix='aegis-', dir=incoming) as tmp_dir:
                            tmp_name = Path(tmp_dir) / safe_name
                            with tmp_name.open('xb') as file:
                                while chunk := uploaded.read(1024 * 1024):
                                    file.write(chunk)
                            result = ingest(tmp_name, db_path)
                    st.session_state['last_import'] = result
                    st.session_state['pending_collection'] = (str(db_path), result['collection_id'])
                    st.rerun()
                except ERRORS as exc:
                    st.error(f'Import gagal: {exc}')
    with right, st.container(border=True, key="panel_workflow"):
        st.subheader('Alur pemeriksaan')
        st.markdown('1. **Impor** ZIP tanpa enkripsi.\n2. **Jalankan assessment** pada Ringkasan.\n3. **Tinjau temuan** dan evidence.\n4. **Ekspor PDF** pada Laporan.')
        st.caption('Simpan ZIP master terpisah. Salinan upload sementara dibersihkan setelah impor.')
    st.stop()

if coll is None:
    st.info('Belum ada collection. Buka Impor ZIP pada sidebar untuk memulai.')
    st.stop()

try:
    artifact_data = store.artifacts(db_path, collection_id)
    cv = store.profile_coverage(db_path, collection_id)
    findings = store.findings(db_path, assessment_id) if assessment_id is not None else []
except ERRORS as exc:
    st.error(f'Gagal membaca collection: {exc}')
    st.stop()

st.caption(f"COLLECTION #{collection_id} · {coll['evidence_count']:,} EVIDENCE ROWS · " +
           (f'ASSESSMENT #{assessment_id}' if assessment_id is not None else 'BELUM ADA ASSESSMENT'))

if page == 'Ringkasan':
    a, b, c, d = st.columns(4)
    a.metric('Evidence tersimpan', f"{coll['evidence_count']:,}")
    b.metric('Artifact Quick', f"{len(cv['present'])}/{cv['required']}")
    c.metric('Rule matches', len(findings) if assessment_id else '—')
    d.metric('Teknik terkait', len({f['technique_id'] for f in findings if f['technique_id']}) if assessment_id else '—')
    st.write('')
    left, right = st.columns([1.8, 1], gap='large')
    with left, st.container(border=True, key="panel_assessment"):
        st.subheader('Hasil assessment')
        if assessment_id is None:
            st.info('Evidence siap dianalisis. Jalankan assessment untuk memeriksa aturan yang tersedia.')
        elif findings:
            st.warning(f'{len(findings)} indikator memerlukan tinjauan. Buka Temuan untuk menelusuri alasan dan evidence.')
            st.caption(' · '.join(f'{level.upper()}: {count}' for level, count in Counter(f['severity'] for f in findings).items()))
        else:
            st.info('Tidak ada rule match pada assessment ini. Hasil ini tidak membuktikan endpoint bersih.')
        if st.button('Jalankan assessment', type='primary'):
            try:
                with st.spinner('Memeriksa rules terhadap evidence...'):
                    result = assess(db_path, rules_path, collection_id)
                st.session_state['last_assessment'] = f"Assessment #{result['assessment_id']} {'digunakan ulang' if result['reused'] else 'dibuat'}: {result['findings_count']} findings"
                st.session_state['pending_assessment'] = (str(db_path), collection_id, result['assessment_id'])
                st.rerun()
            except ERRORS as exc:
                st.error(f'Assessment gagal: {exc}')
    with right, st.container(border=True, key="panel_collection"):
        st.subheader('Konteks koleksi')
        st.text(coll['filename'])
        st.caption('Waktu impor (UTC)')
        st.text(coll['imported_at_utc'])
        st.caption(f'{len(available_assessments)} assessment tersimpan')
        with st.expander('Identitas paket SHA-256'):
            st.code(coll['zip_sha256'], language=None)
    with st.container(border=True, key="panel_artifacts"):
        st.subheader('Artifact yang tersedia')
        st.dataframe(artifact_data, width='stretch', hide_index=True)
        if cv['missing']:
            st.warning('Artifact belum tersedia: ' + ', '.join(cv['missing']))
        st.caption('Coverage mengukur keberadaan artifact, bukan kelengkapan field atau persentase keamanan.')
    with st.expander('Audit ketersediaan field'):
        try:
            for artifact, details in store.normalized_field_audit(db_path, collection_id).items():
                st.text(artifact)
                st.caption(f"{details['rows_with_any_normalized_value']}/{details['rows']} rows memiliki nilai normalisasi")
                st.dataframe([{'Field': k, 'Tersedia': v, 'Total': details['rows']}
                              for k, v in details['field_nonempty_rows'].items()], width='stretch', hide_index=True)
        except ERRORS as exc:
            st.error(f'Audit field gagal: {exc}')

elif page == 'Temuan':
    if assessment_id is None:
        st.info('Jalankan assessment di halaman Ringkasan terlebih dahulu.')
    elif not findings:
        st.info('Tidak ada rule match. Ini tidak menyimpulkan endpoint aman.')
    else:
        a, b, c = st.columns(3)
        counts = Counter(f['severity'] for f in findings)
        for column, level, label in [(a, 'high', 'High'), (b, 'medium', 'Medium'), (c, 'low', 'Low')]:
            column.metric(label, counts[level])
        st.write('')
        left, right = st.columns([1, 2])
        levels = left.multiselect('Severity', ['high', 'medium', 'low'], default=['high', 'medium', 'low'])
        query = right.text_input('Cari rule, judul, atau evidence ID', placeholder='Contoh: POWERSHELL atau T1059.001', key='finding_search')
        filtered = [f for f in findings if f['severity'] in levels and
                    query.casefold() in ' '.join(str(f.get(k) or '') for k in
                    ('rule_id', 'title', 'evidence_id', 'technique_id')).casefold()]
        st.caption(f'{len(filtered)} dari {len(findings)} rule matches ditampilkan')
        if not filtered:
            st.info('Tidak ada temuan sesuai filter. Ubah severity atau kata pencarian.')
        for f in filtered:
            with st.expander(f"[{f['severity'].upper()}] {f['rule_id']} · {f['title']}"):
                st.text(f['reason'])
                st.caption('Observed value')
                st.code(f['observed_value'] or '(tidak tersedia)', language=None)
                st.caption('Evidence ID')
                st.code(f['evidence_id'], language=None)
                st.text(f"Sumber: {f['source_member']} · baris {f['source_row']}")
                st.text(f"MITRE terkait: {f['technique_id'] or 'Unmapped'}")
        st.caption('Beberapa rule matches dapat berasal dari satu aktivitas. Indikator dan asosiasi teknik bukan bukti kompromi.')

elif page == 'MITRE ATT&CK':
    tagged = [f for f in findings if f['technique_id']]
    if not tagged:
        st.info('Belum ada temuan dengan mapping MITRE pada assessment ini.')
    else:
        grouped = Counter((f['tactic'], f['technique_id']) for f in tagged)
        matrix = [{'Taktik': t or 'unspecified', 'Teknik': tech, 'Rule matches': n}
                  for (t, tech), n in sorted(grouped.items())]
        with st.container(border=True, key="panel_mitre"):
            st.subheader('Teknik terkait evidence')
            st.bar_chart(matrix, x='Teknik', y='Rule matches', color='#159b87')
            st.dataframe(matrix, width='stretch', hide_index=True)
    st.caption('Mapping berasal dari subset rules lokal. Teknik yang tidak muncul tidak berarti tidak pernah digunakan.')

elif page == 'Evidence':
    if not findings:
        st.info('Belum ada findings yang dapat ditelusuri. Jalankan assessment di Ringkasan.')
    else:
        targets = {f"#{f['id']} · {f['rule_id']} · {f['evidence_id'][:12]}…": f for f in findings}
        chosen = targets[st.selectbox('Pilih finding', list(targets), key=f'evidence:{db_path}:{assessment_id}')]
        with st.container(border=True, key="panel_evidence"):
            st.subheader('Referensi sumber')
            st.caption('Evidence ID')
            st.code(chosen['evidence_id'], language=None)
            st.text(f"Sumber: {chosen['source_member']}")
            st.text(f"Baris: {chosen['source_row']}")
            reveal_key = f'raw:{db_path}:{collection_id}:{assessment_id}:{chosen["evidence_id"]}'
            if st.checkbox('Tampilkan evidence mentah (bisa berisi data pribadi)', value=False, key=reveal_key):
                item = store.evidence(db_path, chosen['evidence_id'], collection_id)
                if item:
                    st.json({'evidence_id': item['evidence_id'], 'source_member': item['source_member'],
                             'source_row': item['source_row'], 'normalized': item['normalized_json'],
                             'raw': item['raw_json']}, expanded=False)
                else:
                    st.error('Evidence tidak ditemukan di collection terpilih.')

elif page == 'Laporan':
    if assessment_id is None:
        st.info('Jalankan assessment di Ringkasan terlebih dahulu.')
    else:
        left, right = st.columns([1.6, 1], gap='large')
        with left, st.container(border=True, key="panel_report"):
            st.subheader('Siapkan laporan PDF')
            st.text(f'Collection #{collection_id} / Assessment #{assessment_id}')
            st.caption('Assessment aktif mengikuti pilihan pada sidebar.')
            include_observed = st.checkbox('Sertakan observed values yang dapat berisi data sensitif', value=False)
            synthetic_report = st.checkbox('Label sebagai demonstrasi data sintetis', value=False)
            signature = (str(db_path.resolve()), collection_id, assessment_id, include_observed, synthetic_report)
            if st.button('Buat PDF', type='primary'):
                try:
                    from aegis.reporting.pdf_report import load_snapshot, render_pdf
                    with st.spinner('Menyusun laporan...'):
                        content = render_pdf(load_snapshot(db_path, collection_id, assessment_id),
                                             include_observed, synthetic_report)
                    st.session_state['prepared_pdf'] = (signature, content)
                except ERRORS as exc:
                    st.session_state.pop('prepared_pdf', None)
                    st.error(f'Laporan gagal: {exc}')
            prepared = st.session_state.get('prepared_pdf')
            if prepared and prepared[0] == signature:
                st.success('Laporan siap diunduh.')
                st.download_button('Unduh PDF', data=prepared[1],
                                   file_name=f'AEGIS-collection-{collection_id}-assessment-{assessment_id}.pdf',
                                   mime='application/pdf')
        with right, st.container(border=True, key="panel_report_contents"):
            st.subheader('Isi laporan')
            st.markdown('- Ringkasan assessment dan severity\n- Coverage artifact\n- Findings dan mapping MITRE\n- Evidence ID dan baris sumber\n- Hash paket, ruleset, dan batasan')
            st.caption('Raw JSON tidak disertakan. Referensi sumber tetap dapat memuat informasi sensitif.')

st.divider()
st.caption('AEGIS · Triase awal berbasis evidence. Tidak ada temuan bukan bukti endpoint bersih.')
