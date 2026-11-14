"""Чистка data/experiments.csv: настоящие ссылки на источники, дубли, слабые строки.
Исходник сохраняется один раз как data/experiments_raw.csv и каждый запуск читается оттуда.
Запуск: py -3.12 -m pipeline.postprocess   (закройте Excel, если открыт experiments.csv)"""
import pathlib, shutil, urllib.parse
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV, RAW = ROOT / "data" / "experiments.csv", ROOT / "data" / "experiments_raw.csv"
MIN_CONF = 0.6                       # строки с меньшей уверенностью убираем
DROP_IDS = ["19930011018-9"]         # проверено вручную: перегрузка 2 g, не микрогравитация
GUIDE = ("np-2015-10-034-jsc_combustion_in_reduced_gravity-iss-mini-book-011116-508",
         "https://www.nasa.gov/missions/station/a-researchers-guide-to-combustion-science/")

m = dict([GUIDE])
f = ROOT / "urls.txt"
if f.exists():
    for line in f.read_text(encoding="utf-8").splitlines():
        u = line.strip()
        if u.startswith("http"):
            name = pathlib.Path(urllib.parse.unquote(urllib.parse.urlparse(u).path)).name
            m[name[:-4] if name.lower().endswith(".pdf") else name] = u

def link(s):
    s = str(s)
    return "https://ntrs.nasa.gov/citations/" + s if s.isdigit() else m.get(s, s)

if not RAW.exists():
    shutil.copy(CSV, RAW)
df = pd.read_csv(RAW, encoding="utf-8-sig")
n0 = len(df)
nums = ["pressure_kPa", "o2_percent", "flow_speed_cm_s"]
for c in nums + ["extraction_confidence"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df["source_url"] = df["source_url"].map(link)
df["pressure_kPa"] = df["pressure_kPa"].round(1)
df = df[~df["experiment_id"].isin(DROP_IDS)]
df = df.dropna(subset=nums, how="all")
df = df[df["extraction_confidence"].fillna(0) >= MIN_CONF]
df = df.sort_values("extraction_confidence", ascending=False)
df = df.drop_duplicates(subset=["experiment_name", "fuel_or_material", "source_url"] + nums)
df = df.drop_duplicates(subset=["fuel_or_material", "gravity_level", "outcome"] + nums).sort_index()
df.to_csv(CSV, index=False, encoding="utf-8-sig")
print(f"было {n0}, стало {len(df)}")
print(df["phase"].value_counts().to_string())
