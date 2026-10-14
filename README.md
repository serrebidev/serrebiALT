# serrebiALT

AltStore source for serrebidev's iOS apps.

## Add the source

In AltStore, open Sources, tap Add, and paste:

https://raw.githubusercontent.com/serrebidev/serrebiALT/main/apps.json

## Publish an app version

1. Build the app's `.ipa` (needs macOS or a GitHub macOS runner).
2. Run `python add_app.py MyApp.ipa --notes "What changed"`.
   This uploads the `.ipa` to a release in this repo and adds the version to `apps.json`.
   If the `.ipa` is already hosted (for example in the app's own repo releases), pass `--url <download link>` instead.
3. The first time an app is added, fill in its `subtitle`, `localizedDescription`, `iconURL` and `category` in `apps.json`.
4. Commit and push `apps.json`.

The script copies privacy usage descriptions and entitlements from the `.ipa`.
AltStore refuses to install an app whose permissions do not match the source.

Format reference: https://faq.altstore.io/developers/make-a-source
