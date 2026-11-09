# serrebiALT

AltStore source (apps.json) for serrebidev iOS apps. Served from https://altstore.serrebiradio.com/apps.json. That domain proxies the Forgejo raw file (deploy/nginx.conf, live at /etc/nginx/conf.d/altstore.serrebiradio.com.d/source.conf). Forgejo is the source of truth for code, .ipa releases and issues; GitHub, if it returns, is a push mirror only. Never point apps.json or app URLs back at GitHub.

- Add a version: `python add_app.py App.ipa --notes "..."` (uploads to a release here via the Forgejo API; needs FORGEJO_TOKEN, the tea login token works) or with `--url` for an already hosted .ipa. Then commit + push apps.json.
- Versions list is newest first; AltStore treats the first entry as latest. Re-adding an existing version replaces its entry (re-host after a rebuild).
- appPermissions must match the .ipa exactly or AltStore refuses install; add_app.py derives it.
- Test: `python -m pytest -q`.
- Spec: https://faq.altstore.io/developers/make-a-source

## Agent skills

### Issue tracker

Issues are tracked in this repo's Forgejo Issues at git.serrebiradio.com, via the `tea` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
