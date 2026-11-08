"""Whisper worker: JSON lines {path} on stdin -> {text, language} | {error} on stdout. Runs in the mlx venv."""
import json, os, sys
out = os.fdopen(os.dup(1), "w"); sys.stdout = sys.stderr
import numpy as np, mlx.core as mx, mlx_whisper
from mlx_whisper.audio import load_audio
from mlx_whisper.transcribe import ModelHolder
MODEL = "mlx-community/whisper-large-v3-turbo"
ModelHolder.get_model(MODEL, mx.float16)
for line in sys.stdin:
    try:
        a = np.asarray(load_audio(json.loads(line)["path"]))
        if len(a) < 8000 or np.abs(a).max() < 0.01:
            r = dict(text="", language=None)  # under 0.5 s or silence: Whisper invents text
        else:
            t = mlx_whisper.transcribe(a, path_or_hf_repo=MODEL, task="transcribe", verbose=None, condition_on_previous_text=False)
            r = dict(text=t["text"].strip(), language=t["language"])
    except Exception as e:
        r = dict(error=f"{type(e).__name__}: {e}")
    out.write(json.dumps(r, ensure_ascii=False) + "\n"); out.flush()
