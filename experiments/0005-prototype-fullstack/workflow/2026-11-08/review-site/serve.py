#!/usr/bin/env python3
"""Serve the walk-through site with answers and voice notes.

GET  /…                 static files of this directory
GET  /api/answers       {id: latest answer}
POST /api/answer        {id, choice?, note?}      -> feedback/answers.jsonl (append-only, latest per id wins)
POST /api/act           {action, target, result?} -> feedback/actions.jsonl (user action tracking)
POST /api/stt?id=…      audio body -> {text, language, audio}; audio under feedback/audio/, transcript appended to answers as a note
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
            r = json.loads(line); d[r["id"]] = {**d.get(r["id"], {}), **{k: v for k, v in r.items() if v is not None}}
    except FileNotFoundError:
        pass
    return d


def bus(kind, msg):
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
        if u.path == "/api/answer":
            rec = dict(ts=now(), id=str(body["id"]), choice=body.get("choice"), note=body.get("note"))
            append("answers.jsonl", rec); bus("step", f"{rec['id']}: {rec.get('choice') or 'note'}")
            return self.send(200, json.dumps(rec).encode())
        if u.path == "/api/act":
            append("actions.jsonl", dict(ts=now(), source=body.get("source", "mouse"), action=body.get("action"), target=body.get("target"), result=body.get("result")))
            return self.send(200, b"{}")
        return self.send(404, b"{}")


if __name__ == "__main__":
    threading.Thread(target=reaper, daemon=True).start()
    bus("start", "review server up on 127.0.0.1:8768")
    ThreadingHTTPServer(("127.0.0.1", 8768), H).serve_forever()
