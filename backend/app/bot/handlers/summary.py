from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.bot.states import SUMMARY_SELECT_EMPLOYEE, SUMMARY_SELECT_PERIOD
from app.bot.utils import employees_keyboard, period_keyboard, RATING_EMOJI
from app.bot.handlers.start import get_client


async def summary_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    client = get_client(update)
    if not client:
        await update.message.reply_text("Сначала авторизуйся: /start")
        return ConversationHandler.END

    context.user_data["tg_id"] = update.effective_user.id
    employees = await client.get_employees()
    context.user_data["employees"] = {e["employee_id"]: e for e in employees}

    await update.message.reply_text(
        "📊 Выбери сотрудника для summary:",
        reply_markup=employees_keyboard(employees),
    )
    return SUMMARY_SELECT_EMPLOYEE


async def summary_select_employee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    employee_id = query.data.replace("emp_", "")
    employees = context.user_data.get("employees", {})
    context.user_data["summary_employee"] = employees.get(employee_id)

    await query.edit_message_text(
        f"Выбран: {context.user_data['summary_employee']['full_name']}\n\nВыбери период:",
        reply_markup=period_keyboard(),
    )
    return SUMMARY_SELECT_PERIOD


async def summary_select_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    employee = context.user_data["summary_employee"]
    client = get_client(update)

    periods = await client.get_periods()
    if not periods:
        await query.edit_message_text("Активный период не найден. Создай период в администрировании.")
        return ConversationHandler.END

    period = next((p for p in periods if p["is_active"]), periods[0])

    await query.edit_message_text(
        f"⏳ Формирую summary по {employee['full_name']}...\n\nЭто займёт ~15 сек."
    )

    # Пробуем получить готовый summary
    existing = await client.get_summary(employee["employee_id"], period["period_id"])

    # Если нет — генерируем синхронно (ждём LLM)
    if not existing:
        try:
            await client.generate_summary(employee["employee_id"], period["period_id"])
            existing = await client.get_summary(employee["employee_id"], period["period_id"])
        except Exception as e:
            await _safe_edit(query, f"Ошибка генерации: {str(e)[:200]}")
            return ConversationHandler.END

    if not existing:
        history = await client.get_feedback_history(employee["employee_id"], period["period_id"])
        msg = _format_basic_summary(employee, period, history)
    else:
        msg = _format_full_summary(employee, period, existing)

    await _safe_edit(query, msg)
    return ConversationHandler.END


async def _safe_edit(query, text: str):
    try:
        await query.edit_message_text(text, parse_mode="Markdown")
    except Exception:
        try:
            clean = text.replace("*", "").replace("_", "").replace("`", "")
            await query.edit_message_text(clean)
        except Exception:
            pass


def _format_full_summary(employee: dict, period: dict, summary: dict) -> str:
    name = employee["full_name"]
    period_name = period["period_name"]
    total = summary.get("total_feedback_count", 0)
    mapped = summary.get("mapped_feedback_count", 0)
    unmapped = summary.get("unmapped_feedback_count", 0)
    recommendation = summary.get("rating_recommendation") or "insufficient_data"
    rating_emoji = RATING_EMOJI.get(recommendation, "⚪")

    lines = [
        f"📊 *Summary: {name} | {period_name}*\n",
        f"Комментариев: {total} | Размечено: {mapped} | Без критерия: {unmapped}",
        "",
    ]

    top_criteria = summary.get("top_criteria") or []
    if top_criteria:
        lines.append("*Топ критериев:*")
        for i, c in enumerate(top_criteria[:4], 1):
            lines.append(f"{i}. {c.get('criterion_name','?')} — {c.get('mention_count','?')} упоминаний")
        lines.append("")

    strengths = summary.get("strengths") or []
    if strengths:
        lines.append("*Сильные зоны:*")
        for s in strengths[:2]:
            lines.append(f"• {s.get('criterion_name','?')}")
            for q in s.get("evidence_quotes", [])[:1]:
                lines.append(f"  «{str(q)[:100]}»")
        lines.append("")

    growth = summary.get("growth_areas") or []
    if growth:
        lines.append("*Зоны роста:*")
        for g in growth[:2]:
            lines.append(f"• {g.get('criterion_name','?')}")
            for q in g.get("evidence_quotes", [])[:1]:
                lines.append(f"  «{str(q)[:100]}»")
        lines.append("")

    lines.append(f"*Рекомендация:* {rating_emoji} {recommendation}")
    args_against = summary.get("arguments_against") or []
    if args_against:
        lines.append(f"Риск: {str(args_against[0])[:120]}")

    return "\n".join(lines)


def _format_basic_summary(employee: dict, period: dict, feedbacks: list) -> str:
    total = len(feedbacks)
    no_crit = sum(1 for f in feedbacks if f.get("status") == "no_criterion")
    mapped = total - no_crit
    lines = [
        f"📊 *Summary: {employee['full_name']} | {period['period_name']}*\n",
        f"Всего комментариев: {total}",
        f"Размечено: {mapped}",
        f"Без критерия: {no_crit}",
        "",
        "Нет данных для LLM-анализа. Добавь фидбек с разметкой по критериям.",
    ]
    return "\n".join(lines)
