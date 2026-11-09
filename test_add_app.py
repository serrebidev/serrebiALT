import json
import plistlib
import tempfile
import threading
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import add_app
from add_app import add, upload


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
        add(source, ipa, "https://x/Demo3.ipa", "", "2026-10-16")  # rebuild of same version
    app = source["apps"][0]
    assert len(source["apps"]) == 1
    assert app["name"] == "Demo"
    assert app["appPermissions"] == {
        "entitlements": ["com.apple.security.application-groups"],
        "privacy": {"NSMicrophoneUsageDescription": "Record audio."},
    }
    assert [v["downloadURL"] for v in app["versions"]] == ["https://x/Demo3.ipa"]
    assert app["versions"][0]["localizedDescription"] == "Second"
    assert app["versions"][0]["minOSVersion"] == "16.0"


class _ForgejoStub(BaseHTTPRequestHandler):
    seen = {}

    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # No release yet -> upload() must create one.
        self._send(404, {"message": "not found"})

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        raw = self.rfile.read(length)
        type(self).seen[self.path] = (self.headers["Content-Type"], raw)
        if self.path == "/api/v1/repos/serrebi/serrebiALT/releases":
            self._send(201, {"id": 7, "assets": []})
        else:
            assert self.path.startswith("/api/v1/repos/serrebi/serrebiALT/releases/7/assets?name=Demo.ipa")
            self._send(201, {"name": "Demo.ipa"})

    def log_message(self, *a):
        pass


def test_upload_creates_release_and_attaches_ipa(monkeypatch, tmp_path):
    srv = HTTPServer(("127.0.0.1", 0), _ForgejoStub)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setattr(add_app, "FORGEJO", f"http://127.0.0.1:{srv.server_port}")
    monkeypatch.setenv("FORGEJO_TOKEN", "t")
    try:
        ipa = tmp_path / "Demo.ipa"
        ipa.write_bytes(b"fake-ipa-bytes")
        url = upload(ipa, "Demo-v1.2", "notes here")
    finally:
        srv.shutdown()
    assert url == f"http://127.0.0.1:{srv.server_port}/serrebi/serrebiALT/releases/download/Demo-v1.2/Demo.ipa"
    ctype, raw = _ForgejoStub.seen["/api/v1/repos/serrebi/serrebiALT/releases"]
    assert json.loads(raw) == {"tag_name": "Demo-v1.2", "name": "Demo-v1.2", "body": "notes here"}
    ctype, raw = _ForgejoStub.seen["/api/v1/repos/serrebi/serrebiALT/releases/7/assets?name=Demo.ipa"]
    assert ctype.startswith("multipart/form-data")
    assert b'name="attachment"; filename="Demo.ipa"' in raw
    assert b"fake-ipa-bytes" in raw


def test_source_is_hosted_on_forgejo():
    text = add_app.SOURCE.read_text(encoding="utf-8")
    json.loads(text)
    assert "github" not in text.lower()
