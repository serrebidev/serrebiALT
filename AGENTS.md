# serrebiALT

AltStore source (apps.json) for serrebidev iOS apps. Served from raw.githubusercontent.com on main.

- Add a version: `python add_app.py App.ipa --notes "..."` (uploads to a release here via gh) or with `--url` for an already hosted .ipa. Then commit + push apps.json.
- Versions list is newest first; AltStore treats the first entry as latest.
- appPermissions must match the .ipa exactly or AltStore refuses install; add_app.py derives it.
- Test: `python -m pytest -q`.
- Spec: https://faq.altstore.io/developers/make-a-source
