from __future__ import annotations
import json
import httpx
from app.config import settings
from app.llm.prompts import FEEDBACK_ANALYSIS_SYSTEM, build_feedback_analysis_prompt, SUMMARY_SYSTEM, build_summary_prompt


async def _call_llm(system: str, user: str, max_tokens: int = 2048) -> str:
    """Universal LLM call — uses Groq or Anthropic based on settings.llm_provider."""
    if settings.llm_provider == "groq":
        return await _call_groq(system, user, max_tokens)
    else:
        return await _call_anthropic(system, user, max_tokens)


async def _call_groq(system: str, user: str, max_tokens: int) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"},
            json={
                "model": settings.groq_model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _call_anthropic(system: str, user: str, max_tokens: int) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model=settings.llm_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


def _parse_json(raw: str) -> dict | list:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


class FeedbackAnalyzer:
    async def analyze(
        self,
        original_text: str,
        employee_name: str,
        employee_position: str | None,
        employee_level: str | None,
        criteria: list,
    ) -> dict:
        criteria_dicts = [
            {
                "criterion_name": c.criterion_name,
                "below_description": c.below_description,
                "meet_description": c.meet_description,
                "exceeds_description": c.exceeds_description,
            }
            for c in criteria
        ]

        user_prompt = build_feedback_analysis_prompt(
            original_text=original_text,
            employee_name=employee_name,
            employee_position=employee_position,
            employee_level=employee_level,
            criteria=criteria_dicts,
        )

        for attempt in range(2):
            try:
                raw = await _call_llm(FEEDBACK_ANALYSIS_SYSTEM, user_prompt, max_tokens=2048)
                result = _parse_json(raw)
                result["original_text"] = original_text
                return result
            except Exception as e:
                if attempt == 1:
                    return {
                        "original_text": original_text,
                        "needs_clarification": False,
                        "clarification_request": None,
                        "mappings": [],
                        "error": f"Ошибка LLM: {str(e)}",
                    }
        return {"original_text": original_text, "needs_clarification": False, "mappings": []}


class SummaryGenerator:
    async def generate(
        self,
        employee_name: str,
        period_name: str,
        feedbacks: list[dict],
        key_criteria: list[str],
    ) -> dict:
        user_prompt = build_summary_prompt(
            employee_name=employee_name,
            period_name=period_name,
            feedbacks=feedbacks,
            key_criteria=key_criteria,
        )

        for attempt in range(2):
            try:
                raw = await _call_llm(SUMMARY_SYSTEM, user_prompt, max_tokens=4096)
                return _parse_json(raw)
            except Exception:
                if attempt == 1:
                    return _empty_summary()
        return _empty_summary()


def _empty_summary() -> dict:
    return {
        "strengths": [],
        "growth_areas": [],
        "criterion_breakdown": [],
        "top_criteria": [],
        "repeating_patterns": [],
        "recommendation": {
            "rating": "insufficient_data",
            "rationale": "Недостаточно данных",
            "arguments_for": [],
            "arguments_against": [],
            "risks": [],
        },
        "disputed_areas": [],
        "needs_attention": [],
    }
