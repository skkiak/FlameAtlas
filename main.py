import pathlib, re
import pandas as pd
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import ranking, llm

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "experiments.csv"
NUM = ["pressure_kPa", "o2_percent", "flow_speed_cm_s", "spread_rate_mm_s", "extraction_confidence"]

def load():
    df = pd.read_csv(CSV, encoding="utf-8-sig")
    for c in NUM:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=NUM[:3], how="all")  # нужен хотя бы один из трёх параметров
    df = df.astype(object).where(df.notna(), None)
    return df.to_dict("records")

app = FastAPI(title="FlameAtlas")

class Q(BaseModel):
    p: float = 101.3
    o2: float = 21
    flow: float = 10
    phase: str = ""
    question: str = ""

@app.get("/api/experiments")
def experiments():
    return [{"id": r["experiment_id"], "name": r.get("experiment_name") or r["experiment_id"],
             "pl": r.get("platform") or "", "mat": r.get("fuel_or_material") or "",
             "ph": r.get("phase") or "", "p": r["pressure_kPa"], "o": r["o2_percent"],
             "f": r["flow_speed_cm_s"], "r": r["spread_rate_mm_s"], "out": r.get("outcome") or "",
             "kf": r.get("key_finding") or "", "source_url": r.get("source_url") or "",
             "quote": r.get("quote") or "", "confidence": r["extraction_confidence"]} for r in load()]

@app.post("/api/similar")
def similar(q: Q):
    return ranking.top(load(), q.p, q.o2, q.flow, q.phase)

@app.post("/api/chat")
def chat(q: Q):
    o2 = q.o2
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", q.question)  # доля O2 из вопроса важнее слайдера
    if m and 5 <= float(m.group(1).replace(",", ".")) <= 60:
        o2 = float(m.group(1).replace(",", "."))
        # в вопросе названа доля O2: берём 8 экспериментов с ближайшим O2, слайдеры не мешают
        rows = sorted((r for r in load() if r["o2_percent"] is not None
                       and (not q.phase or r["phase"] == q.phase)),
                      key=lambda r: abs(r["o2_percent"] - o2))[:8]
    else:
        rows = ranking.top(load(), q.p, o2, q.flow, q.phase, n=8)
    return {"answer": llm.answer(q.question, rows), "sources": [r["experiment_id"] for r in rows]}

app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="web")
