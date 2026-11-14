"""pdfs/*.pdf -> data/chunks.jsonl (куски ~1500 символов с номером страницы)."""
import json, pathlib, fitz

ROOT = pathlib.Path(__file__).resolve().parent.parent
out = open(ROOT / "data" / "chunks.jsonl", "w", encoding="utf-8")
for pdf in sorted((ROOT / "pdfs").glob("*.pdf")):
    for n, page in enumerate(fitz.open(pdf), 1):
        text = page.get_text().strip()
        for i in range(0, len(text), 1500):
            out.write(json.dumps({"doc": pdf.stem, "page": n, "text": text[i:i+1500]}, ensure_ascii=False) + "\n")
print("готово: data/chunks.jsonl")
