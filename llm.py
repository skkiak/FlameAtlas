import os

SYSTEM = ("Ты помощник по пожарной безопасности в микрогравитации. Отвечай ТОЛЬКО по "
          "пронумерованным источникам ниже, не длиннее 6 предложений, по-русски. Каждое утверждение сопровождай "
          "ссылкой [n]. Если в источниках нет ответа, скажи: «В базе нет данных по этому вопросу». "
          "Значения извлечены ИИ автоматически, при низкой уверенности (extraction_confidence) предупреждай.")
CAP = int(os.getenv("CHAT_CAP", "150"))  # максимум ИИ-ответов за время работы сервера, защита баланса
_used = 0

def _name(r):
    return r.get("experiment_name") or r["experiment_id"]

def _context(rows):
    return "\n".join(
        f"[{i}] {_name(r)} ({r['platform']}), {r['fuel_or_material']}: "
        f"{r['pressure_kPa']} кПа, {r['o2_percent']}% O2, поток {r['flow_speed_cm_s']} см/с, "
        f"гравитация {r.get('gravity_level')}, итог: {r['outcome']}, уверенность {r['extraction_confidence']}, "
        f"цитата: {r['quote'] or 'нет'}"
        for i, r in enumerate(rows, 1))

def _fallback(rows, why):
    r = rows[0]
    return f"{why}: ближайший эксперимент — {_name(r)}, итог: {r['outcome']} [1]."

def answer(question, rows):
    global _used
    if not rows:
        return "В базе нет данных по этому вопросу."
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return _fallback(rows, "ИИ-ответы отключены")
    if _used >= CAP:
        return _fallback(rows, "Лимит ИИ-ответов исчерпан")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key, max_retries=3, timeout=60)
        msg = client.messages.create(
            model=os.getenv("CLAUDE_MODEL", "claude-haiku-5-5"), max_tokens=800, system=SYSTEM,
            messages=[{"role": "user", "content": f"Источники:\n{_context(rows)}\n\nВопрос: {question}"}])
        _used += 1
        return "".join(b.text for b in msg.content if b.type == "text")
    except Exception:
        return _fallback(rows, "ИИ сейчас недоступен")
