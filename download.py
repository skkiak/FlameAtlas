"""Скачивает PDF в pdfs/. Берёт встроенные ссылки + urls.txt (по одной ссылке в строке).
Запуск: python -m pipeline.download"""
import pathlib, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILTIN = [
    # A Researcher's Guide to Combustion Science (NASA, 2015), прямая ссылка на PDF со страницы NASA
    "https://www.nasa.gov/wp-content/uploads/2016/05/np-2015-10-034-jsc_combustion_in_reduced_gravity-iss-mini-book-011116-508.pdf?emrc=c9b273",
]
extra = ROOT / "urls.txt"
urls = BUILTIN + ([u.strip() for u in extra.read_text(encoding="utf-8").splitlines()
                   if u.strip().startswith("http")] if extra.exists() else [])
out = ROOT / "pdfs"; out.mkdir(exist_ok=True)

for u in urls:
    name = pathlib.Path(urllib.parse.unquote(urllib.parse.urlparse(u).path)).name or "doc"
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    dest = out / name
    if dest.exists():
        print("уже есть:", name); continue
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if not data.startswith(b"%PDF"):
            print("не PDF, пропуск:", u); continue
        dest.write_bytes(data); print("скачано:", name, len(data) // 1024, "КБ")
    except Exception as e:
        print("ошибка:", u, e)
