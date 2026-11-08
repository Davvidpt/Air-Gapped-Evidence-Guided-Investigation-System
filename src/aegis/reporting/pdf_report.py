"""Read-only assessment snapshots and local, evidence-linked PDF reports."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
import os
from pathlib import Path
from xml.sax.saxutils import escape

from aegis.detection.engine import report
from aegis.ingestion.importer import summary
from aegis.ui.store import _read_db


def load_snapshot(db_path: Path, collection_id: int, assessment_id: int | None = None) -> dict:
    db = _read_db(db_path)
    try:
        db.execute('BEGIN')
        collection = summary(db, collection_id)
        if assessment_id is None:
            row = db.execute('SELECT id FROM assessment_runs WHERE collection_id=? ORDER BY id DESC LIMIT 1',
                             (collection_id,)).fetchone()
            if row is None:
                raise ValueError('Jalankan assessment sebelum membuat laporan.')
            assessment_id = row['id']
        assessment = report(db, assessment_id)
        if assessment['collection_id'] != collection_id:
            raise ValueError('Assessment bukan milik collection yang dipilih.')
        provenance = {r['evidence_id']: dict(r) for r in db.execute('''
            SELECT evidence_id,source_member,source_row FROM evidence WHERE collection_id=?''', (collection_id,))}
        for finding in assessment['findings']:
            finding.update(provenance[finding['evidence_id']])
        return {'collection': collection, 'assessment': assessment}
    finally:
        db.close()


def render_pdf(snapshot: dict, include_observed: bool = False, synthetic: bool = False) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph
    except ImportError as exc:
        raise RuntimeError('ReportLab belum tersedia. Install dependency: pip install ".[mvp]"') from exc
    collection, assessment = snapshot['collection'], snapshot['assessment']
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles["BodyText"].spaceAfter = 6
    story = []

    def paragraph(value, style='BodyText'):
        # Evidence strings are text, never ReportLab markup, links or images.
        story.append(Paragraph(escape(str(value)), styles[style]))

    paragraph('AEGIS - Laporan Triase Offline', 'Title')
    if synthetic:
        paragraph('DATA SINTETIS - demonstrasi fungsi, bukan hasil pemeriksaan endpoint nyata.', 'Heading2')
    paragraph('Dibuat (UTC): ' + datetime.now(timezone.utc).isoformat())
    paragraph(f"Collection #{collection['collection_id']} / Assessment #{assessment['assessment_id']}")
    paragraph('ZIP SHA-256: ' + collection['zip_sha256'])
    paragraph('Ruleset SHA-256: ' + assessment['ruleset_sha256'])
    paragraph('Engine: ' + assessment['engine_version'])
    paragraph('Ringkasan', 'Heading1')
    paragraph(f"Status: {assessment['status']} | Evidence: {collection['rows']} | Rule matches: {assessment['findings_count']}")
    paragraph('Severity: ' + str(dict(Counter(f['severity'] for f in assessment['findings']))))
    paragraph(assessment['disclaimer'])
    paragraph('Cakupan evidence', 'Heading1')
    coverage = assessment['coverage']
    paragraph(f"Quick artifacts: {len(coverage['present'])}/{coverage['required']}. Ini mengukur keberadaan artifact, bukan efektivitas deteksi atau kelengkapan field.")
    for artifact, count in collection['artifacts'].items():
        paragraph(f'{artifact}: {count} rows')
    paragraph('Artifact belum tersedia: ' + (', '.join(coverage['missing']) or 'Tidak ada pada profil Quick.'))
    paragraph('Temuan dan referensi evidence', 'Heading1')
    if not assessment['findings']:
        paragraph('Tidak ada rule match pada evidence dan ruleset ini. Endpoint tidak dinyatakan bersih.')
    for f in assessment['findings']:
        paragraph(f"{f['rule_id']} [{f['severity'].upper()}] - {f['title']}", 'Heading2')
        paragraph(f['reason'])
        paragraph('MITRE terkait: ' + (f['technique_id'] or 'Unmapped'))
        paragraph('Evidence ID: ' + f['evidence_id'])
        paragraph(f"Sumber: {f['source_member']} / baris {f['source_row']}")
        if include_observed:
            paragraph('Observed value (sensitif): ' + (f['observed_value'] or '-'))
    paragraph('Batasan dan tindak lanjut', 'Heading1')
    paragraph('Temuan adalah indikator untuk ditinjau, bukan vonis infeksi. Mapping ATT&CK hanya subset lokal. Snapshot dapat melewatkan aktivitas yang sudah berakhir. Hash saat impor tidak membuktikan keaslian historis evidence.')
    paragraph('Validasi konteks dan kelengkapan field, telusuri evidence asli, lalu lakukan investigasi lanjutan sesuai SOP organisasi. Simpan ZIP master terpisah dan lindungi akses laporan.')
    paragraph('Observed values disertakan.' if include_observed else 'Observed values dan raw JSON tidak disertakan. Referensi sumber tetap dapat memuat informasi sensitif.')

    def footer(canvas, doc):
        canvas.setFont('Helvetica', 8)
        canvas.drawString(36, 22, 'AEGIS | Triase awal | Lokal / offline')
        canvas.drawRightString(A4[0] - 36, 22, f'Halaman {doc.page}')

    SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36,
                      topMargin=36, bottomMargin=40, title='AEGIS Assessment',
                      author='AEGIS').build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def export_pdf(db_path: Path, collection_id: int, output: Path,
               assessment_id: int | None = None, overwrite: bool = False,
               include_observed: bool = False, synthetic: bool = False) -> Path:
    output = Path(output)
    if output.resolve() == Path(db_path).resolve() or (output.exists() and output.samefile(db_path)):
        raise ValueError('Output tidak boleh menimpa database.')
    content = render_pdf(load_snapshot(db_path, collection_id, assessment_id), include_observed, synthetic)
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if overwrite else os.O_EXCL)
    flags |= getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(output, flags, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(content)
    return output
