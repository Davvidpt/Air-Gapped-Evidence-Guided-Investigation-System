# Upgrade AEGIS M1 -> M2 (Debian, existing database)

**Preserves imported collections and evidence**. Requires Python 3.10+.

1. Place `AEGIS_M2_Patch.zip` in the home directory of the Debian user. Close any other program currently accessing the SQLite DB.
2. Back up the existing DB **before** installing the update:

   ```bash
   cd ~/AEGIS_M1
   cp -p data/aegis-v1.db data/aegis-v1.db.before-m2
   ```

3. Apply update in the repository root:

   ```bash
   unzip -o ~/AEGIS_M2_Patch.zip -d .
   ```

4. Validate tests and the existing M1 import (collection ID 2):

   ```bash
   PYTHONPATH=src python3 -m unittest discover -s tests -v
   PYTHONPATH=src python3 -m aegis inspect-fields --db data/aegis-v1.db --collection 2
   PYTHONPATH=src python3 -m aegis assess --db data/aegis-v1.db --collection 2
   PYTHONPATH=src python3 -m aegis summary --db data/aegis-v1.db --collection 2
   ```

The first database operation will migrate the schema from **v1 to v2** by adding assessment tables. It does not remove existing imported evidence.

**Interpretation**: `REVIEW_REQUIRED` means heuristics matched and need examination. `NO_RULE_MATCHES` is not a clean verdict. Always check `inspect-fields` before interpreting a zero-finding result.

### Demo with fictional indicators (optional)

```bash
python3 scripts/create_assessment_demo.py data/incoming/synthetic-indicators.zip
PYTHONPATH=src python3 -m aegis ingest data/incoming/synthetic-indicators.zip --db data/m2-demo.db
PYTHONPATH=src python3 -m aegis assess --db data/m2-demo.db --collection 1
```

Expected: four findings, three ATT&CK technique associations, and 4/4 quick-profile artifact types available. No real malware is included.

See `docs/12_M2_IMPLEMENTATION.md` for schema, rules, limitations, MITRE references, and acceptance criteria.
