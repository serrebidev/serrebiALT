"""Add an .ipa release to apps.json.

    python add_app.py MyApp.ipa --notes "What changed"
    python add_app.py MyApp.ipa --url https://github.com/serrebidev/MyApp/releases/download/v1.0/MyApp.ipa

Without --url, the .ipa is uploaded to a release in this repo with gh.
"""
import argparse
import datetime
import json
import plistlib
import re
import subprocess
import zipfile
from pathlib import Path

SOURCE = Path(__file__).with_name("apps.json")
REPO = "serrebidev/serrebiALT"
IMPLICIT_ENTITLEMENTS = {"application-identifier", "com.apple.developer.team-identifier"}
PLIST_RE = re.compile(rb"<\?xml.*?</plist>", re.S)


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


def upload(ipa, tag, notes):
    subprocess.run(["gh", "release", "create", tag, str(ipa), "-R", REPO, "-t", tag, "-n", notes], check=True)
    return f"https://github.com/{REPO}/releases/download/{tag}/{ipa.name}"


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
