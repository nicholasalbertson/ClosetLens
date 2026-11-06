# Sovereign Closet / Sovereign Lens

The working app is in [`sovereign-lens/`](sovereign-lens/README.md). Attachments at the repository root are source material and are not served by the app.

```bash
cd sovereign-lens
python3 backend/server.py
```

Open http://127.0.0.1:8080/

```bash
python3 -m pip install pytest
pytest -q sovereign-lens/tests

python3 -m pip install -e "sovereign-lens/repo-bootstrap[dev]"
(cd sovereign-lens/repo-bootstrap && pytest -q)
```

Set `SOVEREIGN_API_KEY` to require `Authorization: Bearer` or `X-API-Key` on `/api/*`. The Lens HTML stays public. Run and limitation notes are in the Lens README.
