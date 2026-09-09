# Backend regression tests

From the repository root, with a Python virtual environment activated:

```sh
python -m pip install -r backend/requirements-dev.txt
python -m pytest backend/tests -q
```

Tests use an isolated in-memory SQLite database with foreign-key enforcement,
test JWT credentials, and a stubbed AI welcome response. They do not connect
to the configured application database or call external AI/music APIs.

Coverage includes populated room deletion, queue ordering when timestamps tie,
duplicate host nicknames, WebSocket membership checks before initial sync,
malformed chat payloads, failed welcome transactions, and sync requests.

Production PostgreSQL and external provider integration are not covered here.
