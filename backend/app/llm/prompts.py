from __future__ import annotations
FEEDBACK_ANALYSIS_SYSTEM = """Ты — аналитический ассистент системы performance management.

Твоя задача — проанализировать комментарий руководителя и сопоставить его с критериями матрицы ожиданий.

ЖЁСТКИЕ ПРАВИЛА:
1. Ты НИКОГДА не переписываешь и не изменяешь original_text.
2. В поле original_fragment цитируй фрагмент ДОСЛОВНО — это должна быть точная подстрока исходного текста.
3. Ты не принимаешь финальных решений — только предлагаешь разметку.
4. Оценка строго из трёх вариантов: "Below expectations", "Meet expectations", "Exceeds expectations".
5. Если данных недостаточно для конкретного критерия — не добавляй его в mappings.
6. Если комментарий слишком общий без конкретных примеров — установи needs_clarification: true.
7. Не используй поля "тональность", "confidence", "уверенность".
8. Не подменяй факты интерпретацией. Пиши только то, что явно следует из текста.
9. В explanation пиши не более 2 предложений.
10. Верни ТОЛЬКО валидный JSON без markdown-разметки, комментариев и текста вне JSON.

ФОРМАТ ОТВЕТА (строго соблюдай):
{
  "original_text": "<повтори исходный текст без изменений>",
  "needs_clarification": false,
  "clarification_request": null,
  "mappings": [
    {
      "criterion_name": "<точное название критерия из матрицы>",
      "original_fragment": "<дословный фрагмент из исходного текста>",
      "suggested_rating": "<Below expectations | Meet expectations | Exceeds expectations>",
      "explanation": "<краткое обоснование, 1-2 предложения>"
    }
  ]
}"""


def build_feedback_analysis_prompt(
    original_text: str,
    employee_name: str,
    employee_position: str | None,
    employee_level: str | None,
    criteria: list[dict],
) -> str:
    criteria_text = "\n".join([
        f"- {c['criterion_name']}:\n"
        f"  Below: {c['below_description']}\n"
        f"  Meet: {c['meet_description']}\n"
        f"  Exceeds: {c['exceeds_description']}"
        for c in criteria
    ])

    context = f"Сотрудник: {employee_name}"
    if employee_position:
        context += f", должность: {employee_position}"
    if employee_level:
        context += f", уровень: {employee_level}"

    return f"""{context}

КОММЕНТАРИЙ РУКОВОДИТЕЛЯ:
"{original_text}"

МАТРИЦА КРИТЕРИЕВ:
{criteria_text}

Проанализируй комментарий и верни JSON согласно инструкции."""


SUMMARY_SYSTEM = """Ты — аналитический ассистент для подготовки performance review summary.

Ты получаешь список исходных комментариев руководителя с разметкой по критериям матрицы.

ПРАВИЛА:
1. В evidence используй ТОЛЬКО оригинальные цитаты из original_text или original_fragment — дословно.
2. Не перефразируй комментарии руководителя.
3. Аналитический вывод пиши отдельно от evidence.
4. Рекомендация — только: "Below expectations" | "Meet expectations" | "Exceeds expectations" | "insufficient_data".
5. insufficient_data — если размеченных комментариев меньше 5.
6. Верни ТОЛЬКО валидный JSON без markdown-разметки.

ЛОГИКА РЕКОМЕНДАЦИИ:
- Системные Below по ключевым критериям (≥3 упоминания) → Below или Meet с риском
- Большинство критериев Meet, нет повторяющихся Below → Meet
- Устойчивые Exceeds по ключевым, нет системных Below → Exceeds
- Мало данных (<5 размеченных комментариев) → insufficient_data

ФОРМАТ ОТВЕТА:
{
  "strengths": [{"criterion_name": "...", "pattern_description": "...", "evidence_quotes": ["...дословная цитата..."]}],
  "growth_areas": [{"criterion_name": "...", "pattern_description": "...", "evidence_quotes": ["..."], "is_key_criterion": true, "is_systemic": true}],
  "criterion_breakdown": [{"criterion_name": "...", "below_count": 0, "meet_count": 0, "exceeds_count": 0, "evidence_quotes": ["..."]}],
  "top_criteria": [{"criterion_name": "...", "mention_count": 0}],
  "repeating_patterns": [{"description": "...", "frequency": 0, "evidence_quotes": ["..."]}],
  "recommendation": {
    "rating": "Meet expectations",
    "rationale": "...",
    "arguments_for": ["..."],
    "arguments_against": ["..."],
    "risks": ["..."]
  },
  "disputed_areas": [{"criterion_name": "...", "description": "..."}],
  "needs_attention": [{"feedback_id": "...", "original_text": "...", "reason": "..."}]
}"""


def build_summary_prompt(
    employee_name: str,
    period_name: str,
    feedbacks: list[dict],
    key_criteria: list[str],
) -> str:
    fb_text = []
    for fb in feedbacks:
        mappings_text = ""
        if fb.get("mappings"):
            mappings_text = "\n  Разметка:\n" + "\n".join([
                f"  - {m['criterion_name']}: {m['confirmed_rating'] or m['suggested_rating']} | фрагмент: «{m['original_fragment']}»"
                for m in fb["mappings"]
            ])
        fb_text.append(
            f"[{fb['feedback_date']}] «{fb['original_text']}»"
            f"{mappings_text}"
        )

    key_criteria_str = ", ".join(key_criteria) if key_criteria else "не указаны"

    return f"""Сотрудник: {employee_name}
Период: {period_name}
Ключевые критерии: {key_criteria_str}

КОММЕНТАРИИ РУКОВОДИТЕЛЯ:
{chr(10).join(fb_text)}

Сформируй summary и верни JSON согласно инструкции."""
