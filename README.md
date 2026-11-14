# FlameAtlas

Демо: https://skkiak.github.io/Flame-Atlas/

NASA Space Apps 2026 · «Flame in Freefall». Дашборд по экспериментам NASA по горению в микрогравитации.

## Запуск
    pip install -r requirements.txt
    cp .env.example .env        # ANTHROPIC_API_KEY нужен только для чата и извлечения
    uvicorn backend.main:app --reload     # откройте http://localhost:8000

Без ключа чат отвечает по шаблону, остальное работает.

## Пайплайн на реальных данных
1. `python -m pipeline.download` скачает PDF по ссылкам из `urls.txt`; другие PDF положить в `pdfs/` вручную (R1).
2. `python -m pipeline.parse_pdfs` даёт `data/chunks.jsonl`.
3. `python -m pipeline.extract` перезаписывает `data/experiments.csv`, кэш в `data/extracted/` (R2).
4. R5 проверяет 20 случайных строк по полю `quote`.

## Важно
`data/experiments.csv` сейчас содержит ДЕМО-строки (`key_finding=MOCK`, уверенность 0). Заменить до сабмита.
Для сабмита описать, как использовался ИИ (извлечение и чат через Claude) и где результаты проверялись вручную.

## Структура
backend/ (FastAPI, ранжирование, LLM) · pipeline/ (парсинг, извлечение) · frontend/ (дашборд) · data/
