"""Streamlit interaction checks with simulated Ant Design navigation."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from io import BytesIO

try:
    from streamlit.testing.v1 import AppTest
    import streamlit_antd_components
except ImportError:
    AppTest = None

from scripts.create_demo_collection import create_zip
from scripts.create_assessment_demo import FAKE_RESULTS
from aegis.ingestion.importer import ingest
from aegis.detection.engine import assess

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = str(ROOT / 'src/aegis/ui/dashboard.py')


@unittest.skipUnless(AppTest, 'Install .[mvp] for Streamlit interaction tests')
class MVPUI(unittest.TestCase):
    def test_first_upload_assessment_evidence_and_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            archive = create_zip(root / 'synthetic.zip', FAKE_RESULTS)
            route = {'page': 'Impor ZIP'}
            with patch('streamlit_antd_components.menu', side_effect=lambda *a, **kw: route['page']):
                app = AppTest.from_file(DASHBOARD).run()
                app.sidebar.text_input[0].set_value(str(root / 'new.db')).run()
                self.assertFalse(app.exception)

                class Upload(BytesIO):
                    name = 'synthetic.zip'
                    size = archive.stat().st_size

                with patch('streamlit.file_uploader', side_effect=lambda *a, **kw: Upload(archive.read_bytes())):
                    app.run()
                    next(b for b in app.button if b.label == 'Validasi & impor ZIP').click().run()
                self.assertFalse(app.exception)
                self.assertTrue((root / 'new.db').is_file())
                route['page'] = 'Ringkasan'
                app.run()
                next(b for b in app.button if b.label == 'Jalankan assessment').click().run()
                self.assertFalse(app.exception)
                self.assertEqual(app.metric[2].value, '4')
                # Reuse the assessment when its selectbox already exists.
                next(b for b in app.button if b.label == 'Jalankan assessment').click().run()
                self.assertFalse(app.exception)
                route['page'] = 'Evidence'
                app.run()
                next(c for c in app.checkbox if c.label.startswith('Tampilkan evidence')).check().run()
                self.assertTrue(app.json)
                route['page'] = 'Laporan'
                app.run()
                try:
                    import reportlab
                except ImportError:
                    return
                next(b for b in app.button if b.label == 'Buat PDF').click().run()
                self.assertFalse(app.exception)
                self.assertTrue(app.get('download_button'))
                app.run()
                self.assertTrue(app.get('download_button'))
                app.checkbox[0].check().run()
                self.assertFalse(app.get('download_button'))

    def test_findings_filter_and_empty_states(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            archive = create_zip(root/'positive.zip', FAKE_RESULTS)
            db = root/'demo.db'
            cid = ingest(archive, db)['collection_id']
            assess(db, ROOT/'rules/detection.json', cid)
            route = {'page': 'Temuan'}
            with patch('streamlit_antd_components.menu', side_effect=lambda *a, **kw: route['page']):
                app = AppTest.from_file(DASHBOARD).run()
                app.sidebar.text_input[0].set_value(str(db)).run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.expander), 5)  # settings + four findings
                app.multiselect[0].set_value(['low']).run()
                self.assertEqual(len(app.expander), 2)
                app.text_input(key='finding_search').set_value('no-such-rule').run()
                self.assertTrue(any('Tidak ada temuan sesuai filter' in x.value for x in app.info))
                route['page'] = 'MITRE ATT&CK'
                app.run()
                self.assertFalse(app.exception)
                self.assertTrue(app.dataframe)
                for page in ('Ringkasan', 'Temuan', 'MITRE ATT&CK', 'Evidence', 'Laporan'):
                    route['page'] = page
                    app.sidebar.text_input[0].set_value(str(root/'absent.db')).run()
                    self.assertFalse(app.exception)
                    self.assertTrue(app.info)

    def test_real_community_menu_renders(self):
        # AppTest cannot click iframe components, but verifies serialization.
        app = AppTest.from_file(DASHBOARD).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.get('component_instance'))
