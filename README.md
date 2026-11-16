# serrebiALT

AltStore source for serrebidev's iOS apps.

[![Join SerrebiProjects on Telegram](https://img.shields.io/badge/Telegram-SerrebiProjects-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/SerrebiProjects)

**Questions, bugs, or release news?** Join the [SerrebiProjects Telegram group](https://t.me/SerrebiProjects), the fastest place to get help.

More serrebi projects: [projects.serrebiradio.com](https://projects.serrebiradio.com)

## Add the source

In AltStore, open Sources, tap Add, and paste:

https://altstore.serrebiradio.com/apps.json

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

## Credits

See [CREDITS.md](CREDITS.md) for where the ideas behind this project came from, and the third-party projects it builds on.
