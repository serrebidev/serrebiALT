import plistlib
import tempfile
import zipfile
from pathlib import Path

from add_app import add


def test_add_reads_ipa():
    info = {
        "CFBundleIdentifier": "com.serrebidev.demo",
        "CFBundleDisplayName": "Demo",
        "CFBundleExecutable": "Demo",
        "CFBundleShortVersionString": "1.2",
        "CFBundleVersion": "7",
        "MinimumOSVersion": "16.0",
        "NSMicrophoneUsageDescription": "Record audio.",
    }
    ents = {"application-identifier": "T.com.serrebidev.demo", "com.apple.security.application-groups": ["g"]}
    with tempfile.TemporaryDirectory() as d:
        ipa = Path(d) / "Demo.ipa"
        with zipfile.ZipFile(ipa, "w") as z:
            z.writestr("Payload/Demo.app/Info.plist", plistlib.dumps(info))
            z.writestr("Payload/Demo.app/Demo", b"\xcf\xfa\xed\xfe junk " + plistlib.dumps(ents) + b" more")
        source = {"apps": []}
        add(source, ipa, "https://x/Demo.ipa", "First", "2026-10-14")
        add(source, ipa, "https://x/Demo2.ipa", "Second", "2026-10-15")
    app = source["apps"][0]
    assert len(source["apps"]) == 1
    assert app["name"] == "Demo"
    assert app["appPermissions"] == {
        "entitlements": ["com.apple.security.application-groups"],
        "privacy": {"NSMicrophoneUsageDescription": "Record audio."},
    }
    assert [v["downloadURL"] for v in app["versions"]] == ["https://x/Demo2.ipa", "https://x/Demo.ipa"]
    assert app["versions"][0]["minOSVersion"] == "16.0"
