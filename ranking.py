import math
# параметр: (вес, масштаб нормировки)
W = {"pressure_kPa": (0.25, 90), "o2_percent": (0.5, 25), "flow_speed_cm_s": (0.25, 40)}

def similarity(r, p, o2, f):
    vals = {"pressure_kPa": p, "o2_percent": o2, "flow_speed_cm_s": f}
    s = w = 0.0
    for k, (wt, rng) in W.items():
        v = r.get(k)
        if v in (None, ""):
            continue  # параметр не извлечён: считаем по тем, что есть
        s += wt * ((vals[k] - v) / rng) ** 2
        w += wt
    if w == 0:
        return 0.0
    # чем меньше параметров известно, тем ниже итоговая оценка
    return max(0.0, (1 - math.sqrt(s / w) * 1.6) * w)

def top(rows, p, o2, f, phase="", n=5):
    scored = [(similarity(r, p, o2, f), r) for r in rows if not phase or r.get("phase") == phase]
    scored.sort(key=lambda t: t[0], reverse=True)
    return [dict(r, similarity=round(s, 3)) for s, r in scored[:n]]
