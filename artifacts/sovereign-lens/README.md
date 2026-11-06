## Backend UI + Auth

- `backend-ui.html` — dedicated UI for the backend (status, compose, twin prompt, products)
- `docs/API-AUTH.md` — API key, Gemini, Google Photos OAuth, and future options

Run the server (optional auth):
```bash
cd sovereign-lens
export SOVEREIGN_API_KEY=dev-key   # or omit for open mode
python3 backend/server.py
```
Open `backend-ui.html` and set base URL to `http://localhost:8080`.