# serrebiALT

AltStore source (apps.json) for serrebidev iOS apps. Served from raw.githubusercontent.com on main.

- Add a version: `python add_app.py App.ipa --notes "..."` (uploads to a release here via gh) or with `--url` for an already hosted .ipa. Then commit + push apps.json.
- Versions list is newest first; AltStore treats the first entry as latest.
- appPermissions must match the .ipa exactly or AltStore refuses install; add_app.py derives it.
- Test: `python -m pytest -q`.
- Spec: https://faq.altstore.io/developers/make-a-source

## Agent skills

### Issue tracker

Issues are tracked in this repo's GitHub Issues, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
