#!/usr/bin/env python3
"""Serve the walk-through site with answers and voice notes.

GET  /…                 static files of this directory
GET  /api/answers       {id: latest answer, with choice_ts / note_ts}
POST /api/answer        {id, choice?, note?}      -> feedback/answers.jsonl (append-only, latest per id wins;
                        choice "" or note "" clears it in the merged view, the history stays in the file)
GET  /api/current       feedback/current.json {id, ts} (the question the main agent shows on next.html); 404 {} if none
GET  /api/version       {site, explain}: newest mtime of *.html/*.css/*.js here and of explain/*.html (cached 1 s);
                        pages reload when `site` changes, next.html reloads its fragment by itself
POST /api/current       {id} -> sets it; CLI: python3 serve.py current QF-2
POST /api/act           {action, target, result?} -> feedback/actions.jsonl (user action tracking)
POST /api/stt?id=…      audio body -> {text, language, audio}; audio under feedback/audio/, transcript appended to answers as a note
Port: argv[1], default 8768. REVIEW_NO_BUS=1 keeps a test copy off the job bus.
Whisper: the mlx venv of the rating desk (dreamid-v tools/rate/venv), model whisper-large-v3-turbo, worker started on
first use, stopped after 10 min idle. Without the venv, /api/stt answers 503 and the page falls back to typing.
"""
import datetime as dt, json, os, select, subprocess, sys, threading, time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
FB = HERE / "feedback"; AUDIO = FB / "audio"
VENV_PY = Path.home() / "Projects/dreamid-v/tools/rate/venv/bin/python"
LOCK = threading.Lock(); STT = dict(p=None, last=0.0); STT_LOCK = threading.Lock(); IDLE = 600
EXT = {"audio/webm": "webm", "audio/mp4": "m4a", "audio/ogg": "ogg", "audio/wav": "wav"}


def now(): return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append(name, rec):
    FB.mkdir(exist_ok=True)
    with LOCK, open(FB / name, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def answers():
    d = {}
    try:
        for line in open(FB / "answers.jsonl"):
            r = json.loads(line); a = d.setdefault(r["id"], {})
            a.update({k: v for k, v in r.items() if v is not None and k != "note"})
            if r.get("choice") is not None: a["choice_ts"] = r["ts"]
            if a.get("choice") == "": a.pop("choice"); a.pop("choice_ts", None)
            if r.get("note"):  # every note is kept; the page shows them all, oldest first
                a.setdefault("notes", []).append({"ts": r["ts"], "text": r["note"]})
                a["note"] = r["note"]; a["note_ts"] = r["ts"]
            elif r.get("note") == "":
                a.pop("notes", None); a.pop("note", None); a.pop("note_ts", None)
    except FileNotFoundError:
        pass
    return d


CUR = FB / "current.json"


def set_current(item, source):
    rec = dict(id=str(item), ts=now()); FB.mkdir(exist_ok=True)
    tmp = CUR.with_suffix(".tmp"); tmp.write_text(json.dumps(rec, ensure_ascii=False)); tmp.replace(CUR)  # atomic for the 3 s poll
    append("actions.jsonl", dict(ts=rec["ts"], source=source, action="set-current", target=rec["id"], result="ok"))
    return rec


VER = dict(t=0.0, v=None)


def version():
    if time.time() - VER["t"] > 1:
        m = lambda ps: max((p.stat().st_mtime for p in ps), default=0)
        VER["v"] = dict(site=m(p for e in ("*.html", "*.css", "*.js") for p in HERE.glob(e)), explain=m((HERE / "explain").glob("*.html")))
        VER["t"] = time.time()
    return VER["v"]


def bus(kind, msg):
    if os.environ.get("REVIEW_NO_BUS"): return
    try:
        sys.path.insert(0, os.path.expanduser("~/.claude-bus")); from cbus import post
        post("review-d037", kind, msg=msg, title="Review the 0005 DEFAULTS (OWNER walk-through)")
    except Exception:
        pass


def worker():
    p = STT["p"]
    if not p or p.poll() is not None:
        FB.mkdir(exist_ok=True)
        env = dict(os.environ, HF_HUB_OFFLINE="1", PATH="/opt/homebrew/bin:" + os.environ.get("PATH", ""))
        p = STT["p"] = subprocess.Popen([str(VENV_PY), str(HERE / "stt_worker.py")], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=open(FB / "stt.log", "a"), text=True, env=env)
    STT["last"] = time.time(); return p


def transcribe(path):
    if not VENV_PY.exists(): raise RuntimeError("no whisper venv")
    with STT_LOCK:
        p = worker(); p.stdin.write(json.dumps({"path": str(path)}) + "\n"); p.stdin.flush()
        if not select.select([p.stdout], [], [], 180)[0]: p.kill(); raise RuntimeError("whisper timeout")
        line = p.stdout.readline(); STT["last"] = time.time()
    if not line: raise RuntimeError("whisper worker died (see feedback/stt.log)")
    r = json.loads(line)
    if "error" in r: raise RuntimeError(r["error"])
    return r


def warm():
    with STT_LOCK: worker()


def reaper():
    while True:
        time.sleep(30)
        with STT_LOCK:
            p = STT["p"]
            if p and p.poll() is None and time.time() - STT["last"] > IDLE: p.terminate(); STT["p"] = None


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(HERE), **k)
    def log_message(self, *a): pass

    def send(self, code, body):
        self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if urlsplit(self.path).path == "/api/answers": return self.send(200, json.dumps(answers()).encode())
        if urlsplit(self.path).path == "/api/stt": return self.send(200, json.dumps({"ok": VENV_PY.exists()}).encode())
        if urlsplit(self.path).path == "/api/version": return self.send(200, json.dumps(version()).encode())
        if urlsplit(self.path).path == "/api/current":
            return self.send(200, CUR.read_bytes()) if CUR.exists() else self.send(404, b"{}")
        if self.path.startswith("/feedback/"): return self.send(404, b"{}")
        return super().do_GET()

    def do_POST(self):
        u = urlsplit(self.path); n = int(self.headers.get("Content-Length") or 0)
        if u.path == "/api/stt/warm":
            if VENV_PY.exists(): threading.Thread(target=warm, daemon=True).start()
            return self.send(200, b"{}")
        if u.path == "/api/stt":
            if n > 20 << 20: return self.send(413, b'{"error": "clip over 20 MB"}')
            item = parse_qs(u.query).get("id", [""])[0]
            ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
            AUDIO.mkdir(parents=True, exist_ok=True)
            name = f"{now().replace(':', '')}-{''.join(c for c in item if c.isalnum() or c in '-_')}.{EXT.get(ctype, 'webm')}"
            (AUDIO / name).write_bytes(self.rfile.read(n))
            try:
                r = transcribe(AUDIO / name)
            except Exception as e:
                append("actions.jsonl", dict(ts=now(), source="voice", action="stt", target=item, result=f"error: {e}"))
                return self.send(503, json.dumps({"error": str(e), "audio": name}).encode())
            append("actions.jsonl", dict(ts=now(), source="voice", action="stt", target=item, result="ok", chars=len(r["text"])))
            if r["text"]:
                append("answers.jsonl", dict(ts=now(), id=item, note=r["text"], audio=name)); bus("step", f"voice note on {item}")
            return self.send(200, json.dumps(dict(r, audio=name), ensure_ascii=False).encode())
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self.send(400, b'{"error": "bad json"}')
        if u.path == "/api/current":
            if not str(body.get("id") or "").strip(): return self.send(400, b'{"error": "id missing"}')
            return self.send(200, json.dumps(set_current(body["id"], "api"), ensure_ascii=False).encode())
        if u.path == "/api/answer":
            rec = dict(ts=now(), id=str(body["id"]), choice=body.get("choice"), note=body.get("note"))
            append("answers.jsonl", rec); bus("step", f"{rec['id']}: {rec.get('choice') or 'note'}")
            return self.send(200, json.dumps(rec).encode())
        if u.path == "/api/act":
            append("actions.jsonl", dict(ts=now(), source=body.get("source", "mouse"), action=body.get("action"), target=body.get("target"), result=body.get("result")))
            return self.send(200, b"{}")
        return self.send(404, b"{}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["current"]:
        print(json.dumps(set_current(sys.argv[2], "cli"), ensure_ascii=False)); sys.exit()
    threading.Thread(target=reaper, daemon=True).start()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8768
    bus("start", f"review server up on 127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
