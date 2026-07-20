import requests
import itertools
import re
from collections import Counter
from src.config import OLLAMA_BASE_URL, MODEL_NAME

def generate_response(prompt: str, params: dict) -> str:
    """Отправляет запрос к Ollama и возвращает текст"""
    
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    payload = {
        "model": MODEL_NAME, 
        "prompt": prompt, 
        "stream": False, 
        "options": params
    }
    try:
        response = requests.post(url, json=payload, timeout=300).json()
        return response.get("response", "").strip()
    except Exception as e:
        return f"Ошибка: {e}"

def score_response(text: str) -> tuple[int, dict]:
    """
    Эвристическая функция оценки ответа для агрономической задачи.
    Шкала: 0–100 баллов.
    """
    score = 50
    details = {"length": len(text), "penalties": [], "bonuses": []}
    text_lower = text.lower()

    # 1. Релевантность
    keywords_good = ["пшениц", "колошен", "стресс", "азот", "влаг", "нитроген",
                     "рекоменд", "удобрен", "почв", "корнев", "лист", "фотосинтез",
                     "засух", "дефицит", "болезн", "вредител"]
    matches_good = [kw for kw in keywords_good if kw in text_lower]
    unique_matches = len(set(matches_good))
    score += min(unique_matches * 4, 20)
    details["bonuses"].append(f"Релевантность: {unique_matches} терминов")

    # 2. Галлюцинации
    if re.search(r'урожайность \d+ ц/га', text_lower) or re.search(r'вносить \d+ кг', text_lower):
        score -= 25
        details["penalties"].append("Выдуманные конкретные цифры")

    # 3. Повторы фраз
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
    sentence_counts = Counter(sentences)
    repeated = sum(1 for c in sentence_counts.values() if c > 1)
    if repeated > 0:
        score -= 5 * repeated
        details["penalties"].append(f"Повторы фраз: {repeated}")

    # 4. Пропорциональный штраф за длину
    text_len = len(text)
    if text_len > 1100:
        excess = text_len - 1100
        penalty = min(5 + (excess // 200) * 5, 35)
        score -= penalty
        details["penalties"].append(f"Длина {text_len} символов, превышение на {excess})")
    elif text_len < 200:
        score -= 30
        details["penalties"].append(f"Слишком короткий: {text_len} символов")
    elif 400 <= text_len <= 900:
        score += 7
        details["bonuses"].append(f"Оптимальная длина: {text_len}")

    # 5. Структура
    if "-" in text or "1." in text or "во-первых" in text_lower or "•" in text:
        score += 5
        details["bonuses"].append("Хорошая структура")

    # 6. Риски
    risk_patterns = [
        r'\d+[.)]\s*([^\n]*(?:стресс|засух|дефицит|болезн|вредител)[^\n]*)',
        r'[-•]\s*([^\n]*(?:стресс|засух|дефицит|болезн|вредител)[^\n]*)'
    ]
    risks_found = sum(len(re.findall(p, text_lower)) for p in risk_patterns)
    if 2 <= risks_found <= 3:
        score += 10
        details["bonuses"].append(f"Рисков: {risks_found} — оптимально")
    elif risks_found == 1:
        score += 3
        details["bonuses"].append(f"Рисков: {risks_found} — мало")
    elif risks_found > 3:
        score += 5
        details["bonuses"].append(f"Рисков: {risks_found} — избыточно")

    # 7. Рекомендация
    if re.search(r'рекоменд(ую|ация|ации|аций)', text_lower):
        score += 3
        details["bonuses"].append("Есть рекомендация")

    # 8. Плотность информации
    if text_len > 0:
        info_density = unique_matches / (text_len / 100)
        if info_density > 0.6:
            score += 5
            details["bonuses"].append(f"Высокая плотность: {info_density:.2f}")
        elif info_density > 0.35:
            score += 3
            details["bonuses"].append(f"Средняя плотность: {info_density:.2f}")
        elif info_density > 0.15:
            score += 1
            details["bonuses"].append(f"Низкая плотность: {info_density:.2f}")

    return max(0, score), details

if __name__ == "__main__":
    test_prompt = (
        "Кратко объясни, что означает NDVI = 0.45 для пшеницы в фазе колошения. "
        "Перечисли 2-3 конкретных агрономических риска и одну рекомендацию. "
        "Не выдумывай точные цифры урожайности или норм внесения, если они не даны."
    )
    
    print(f"Запуск Grid Search для модели: {MODEL_NAME}")
    print(f"Промпт: {test_prompt}\n" + "="*80)

    search_space = {
        "temperature": [0.2, 0.5, 0.7],
        "top_p": [0.7, 0.85, 0.95],
        "top_k": [30, 50],
        "num_predict": [512, 1024]
    }

    keys, values = zip(*search_space.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    results = []

    print(f"Всего комбинаций для проверки: {len(combinations)}")

    for i, params in enumerate(combinations, 1):
        print(f"[{i}/{len(combinations)}] Тестируем: {params} ... ", end="", flush=True)
        
        response_text = generate_response(test_prompt, params)
        score, details = score_response(response_text)
        
        results.append({
            "params": params,
            "score": score,
            "response_preview": response_text[:150] + "..." if len(response_text) > 150 else response_text,
            "details": details
        })
        print(f"Оценка: {score}/100 (длина: {details['length']} символов)")

    results.sort(key=lambda x: x["score"], reverse=True)

    print("\n" + "="*80)
    print("ТОП-3 ЛУЧШИЕ КОНФИГУРАЦИИ:")
    print("="*80)
    
    for rank, res in enumerate(results[:3], 1):
        print(f"\n{rank} место (Оценка: {res['score']}/100)")
        print(f"Параметры: {res['params']}")
        print(f"Плюсы: {', '.join(res['details']['bonuses']) if res['details']['bonuses'] else 'Нет'}")
        print(f"Минусы: {', '.join(res['details']['penalties']) if res['details']['penalties'] else 'Нет'}")
        print(f"Пример ответа: {res['response_preview']}")