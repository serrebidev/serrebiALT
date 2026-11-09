# serrebiALT

AltStore source for serrebidev's iOS apps.

## Add the source

In AltStore, open Sources, tap Add, and paste:

https://git.serrebiradio.com/serrebi/serrebiALT/raw/branch/main/apps.json

## Publish an app version

1. Build the app's `.ipa` (needs macOS).
2. Run `python add_app.py MyApp.ipa --notes "What changed"` with `FORGEJO_TOKEN` set to a Forgejo token that can write releases.
   This uploads the `.ipa` to a release in this repo on git.serrebiradio.com and adds the version to `apps.json`.
   If the `.ipa` is already hosted (for example in the app's own Forgejo releases), pass `--url <download link>` instead.
   Adding a version that is already listed replaces that entry, so a rebuilt `.ipa` can re-host a lost download.
3. The first time an app is added, fill in its `subtitle`, `localizedDescription`, `iconURL` and `category` in `apps.json`.
4. Commit and push `apps.json` to Forgejo.

Forgejo (git.serrebiradio.com) hosts the source, the `.ipa` files and the issues.
A GitHub copy, if one exists, is only a mirror: never point `apps.json` at it.

The script copies privacy usage descriptions and entitlements from the `.ipa`.
AltStore refuses to install an app whose permissions do not match the source.

Format reference: https://faq.altstore.io/developers/make-a-source
