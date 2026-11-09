"""Add an .ipa release to apps.json.

    python add_app.py MyApp.ipa --notes "What changed"
    python add_app.py MyApp.ipa --url https://git.serrebiradio.com/serrebi/MyApp/releases/download/v1.0/MyApp.ipa

Without --url, the .ipa is uploaded to a release in this repo via the
Forgejo API. Needs FORGEJO_TOKEN in the environment.
"""
import argparse
import datetime
import json
import os
import plistlib
import re
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

SOURCE = Path(__file__).with_name("apps.json")
FORGEJO = "https://git.serrebiradio.com"
REPO = "serrebi/serrebiALT"
IMPLICIT_ENTITLEMENTS = {"application-identifier", "com.apple.developer.team-identifier"}
# A blob never spans another XML header: large binaries carry stray "<?xml" strings.
PLIST_RE = re.compile(rb"<\?xml(?:(?!<\?xml).)*?</plist>", re.S)


def read_ipa(ipa):
    """Return (Info.plist dict, entitlements set) for the app and its extensions."""
    with zipfile.ZipFile(ipa) as z:
        names = z.namelist()
        info_name = next(n for n in names if re.fullmatch(r"Payload/[^/]+\.app/Info\.plist", n))
        info = plistlib.loads(z.read(info_name))
        entitlements = set()
        for plist_name in names:
            if not plist_name.endswith(".app/Info.plist") and not plist_name.endswith(".appex/Info.plist"):
                continue
            bundle_info = plistlib.loads(z.read(plist_name))
            exe = plist_name.rsplit("/", 1)[0] + "/" + bundle_info.get("CFBundleExecutable", "")
            if exe not in names:
                continue
            # ponytail: scans the signed binary for embedded XML plists instead of parsing Mach-O;
            # use ldid/codesign output if an app ever ships entitlements in DER only.
            for blob in PLIST_RE.findall(z.read(exe)):
                try:
                    d = plistlib.loads(blob)
                except Exception:
                    continue
                if isinstance(d, dict) and "application-identifier" in d:
                    entitlements |= d.keys()
        return info, sorted(entitlements - IMPLICIT_ENTITLEMENTS)


def _api(path, token, data=None, method="GET"):
    req = urllib.request.Request(
        f"{FORGEJO}/api/v1/repos/{REPO}{path}",
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Forgejo API {method} {path} failed: {e.code} {e.read().decode()[:300]}") from e


def _get_release(tag, token):
    try:
        return _api(f"/releases/tags/{urllib.parse.quote(tag, safe='')}", token)
    except RuntimeError as e:
        if " 404 " in str(e):
            return None
        raise


def _upload_asset(release_id, ipa, token):
    # Forgejo expects the file in the multipart field named "attachment".
    boundary = "----serrebiALTipa"
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="attachment"; filename="{ipa.name}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + ipa.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{FORGEJO}/api/v1/repos/{REPO}/releases/{release_id}/assets?name={urllib.parse.quote(ipa.name)}",
        data=body,
        headers={"Authorization": f"token {token}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Forgejo asset upload failed: {e.code} {e.read().decode()[:300]}") from e


def upload(ipa, tag, notes):
    token = os.environ.get("FORGEJO_TOKEN")
    if not token:
        raise RuntimeError("FORGEJO_TOKEN is not set")
    release = _get_release(tag, token)
    if release is None:
        release = _api("/releases", token, {"tag_name": tag, "name": tag, "body": notes}, method="POST")
    if not any(a["name"] == ipa.name for a in release.get("assets", [])):
        _upload_asset(release["id"], ipa, token)
    return f"{FORGEJO}/{REPO}/releases/download/{tag}/{ipa.name}"


def add(source, ipa, url, notes, today):
    info, entitlements = read_ipa(ipa)
    bundle_id = info["CFBundleIdentifier"]
    app = next((a for a in source["apps"] if a["bundleIdentifier"] == bundle_id), None)
    if app is None:
        name = info.get("CFBundleDisplayName") or info.get("CFBundleName") or bundle_id
        app = {
            "name": name,
            "bundleIdentifier": bundle_id,
            "developerName": "serrebidev",
            "subtitle": "",
            "localizedDescription": name,
            "iconURL": "",
            "category": "utilities",
            "screenshots": [],
            "versions": [],
        }
        source["apps"].append(app)
    app["appPermissions"] = {
        "entitlements": entitlements,
        "privacy": {k: v for k, v in info.items() if k.endswith("UsageDescription")},
    }
    version = {
        "version": info["CFBundleShortVersionString"],
        "buildVersion": info["CFBundleVersion"],
        "date": today,
        "localizedDescription": notes,
        "downloadURL": url,
        "size": ipa.stat().st_size,
    }
    if "MinimumOSVersion" in info:
        version["minOSVersion"] = info["MinimumOSVersion"]
    old = next((v for v in app["versions"] if v["version"] == version["version"]), None)
    if old is not None:
        # Re-hosting a rebuilt version (e.g. after losing the GitHub assets): replace in place.
        if not notes:
            version["localizedDescription"] = old["localizedDescription"]
        app["versions"][app["versions"].index(old)] = version
    else:
        app["versions"].insert(0, version)  # first = latest
    return app


def main():
    p = argparse.ArgumentParser()
    p.add_argument("ipa", type=Path)
    p.add_argument("--url", help="download URL if the .ipa is already hosted")
    p.add_argument("--notes", default="")
    args = p.parse_args()
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    info, _ = read_ipa(args.ipa)
    tag = f"{info['CFBundleIdentifier'].rsplit('.', 1)[-1]}-v{info['CFBundleShortVersionString']}"
    url = args.url or upload(args.ipa, tag, args.notes)
    app = add(source, args.ipa, url, args.notes, datetime.date.today().isoformat())
    SOURCE.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Added {app['name']} {app['versions'][0]['version']}. Commit and push apps.json.")


if __name__ == "__main__":
    main()
