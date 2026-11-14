"""chunks.jsonl -> data/extracted/<doc>.jsonl (кэш) -> data/experiments.csv."""
import json, os, pathlib, re, collections
import anthropic, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "extracted"; CACHE.mkdir(exist_ok=True)
KEYS = re.compile(r"oxygen|O2|pressure|flow|ignit|extinct|spread|кислород", re.I)
COLS = ["experiment_id", "experiment_name", "platform", "year", "fuel_or_material", "phase",
        "pressure_kPa", "o2_percent", "flow_speed_cm_s", "gravity_level", "outcome",
        "spread_rate_mm_s", "key_finding", "source_url", "quote", "extraction_confidence"]
PROMPT = """Из текста статьи извлеки ВСЕ эксперименты по горению с числовыми условиями.
Верни ТОЛЬКО JSON Lines: по одному JSON-объекту на строку, без массива, без markdown, без пояснений.
Поля: experiment_name, platform, year, fuel_or_material, phase (solid|liquid|gas),
pressure_kPa, o2_percent, flow_speed_cm_s, gravity_level, outcome, spread_rate_mm_s,
key_finding, quote, extraction_confidence (0-1).
quote: дословная цитата из текста, подтверждающая числа, не длиннее 200 символов, без переносов
строк, двойные кавычки внутри цитаты замени на одинарные.
Приводи единицы к кПа, %, см/с. Если значения нет в тексте, ставь null. Ничего не выдумывай."""

docs = collections.defaultdict(list)
for line in open(ROOT / "data" / "chunks.jsonl", encoding="utf-8"):
    c = json.loads(line)
    if KEYS.search(c["text"]):
        docs[c["doc"]].append(c["text"])

client = anthropic.Anthropic(max_retries=6, timeout=120)
rows, bad = [], 0
for doc, texts in docs.items():
    f = CACHE / f"{doc}.jsonl"
    if not f.exists():
        msg = client.messages.create(model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"), max_tokens=8000,
            messages=[{"role": "user", "content": PROMPT + "\n\n" + "\n---\n".join(texts)[:60000]}])
        print(doc[:30], "stop_reason:", msg.stop_reason)
        f.write_text("".join(b.text for b in msg.content if b.type == "text"), encoding="utf-8")
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip().strip("`")
        if not line.startswith("{"):
            continue
        try:
            r = json.loads(line)
        except Exception:
            bad += 1
            continue
        r["experiment_id"] = f"{doc[:20]}-{len(rows) + 1}"
        r["source_url"] = r.get("source_url") or doc
        rows.append(r)

print(len(rows), "экспериментов, пропущено битых строк:", bad)
if rows:
    out = pd.DataFrame(rows).reindex(columns=COLS)
    out.to_csv(ROOT / "data" / "experiments.csv", index=False, encoding="utf-8-sig")
    print("записано в data/experiments.csv; проверьте 20 случайных вручную (роль R5)")
else:
    print("experiments.csv НЕ изменён")