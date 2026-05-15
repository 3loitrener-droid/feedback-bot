from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.bot.states import HISTORY_SELECT_EMPLOYEE
from app.bot.utils import employees_keyboard, STATUS_LABELS, RATING_EMOJI
from app.bot.handlers.start import get_client


async def history_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    client = get_client(update)
    if not client:
        await update.message.reply_text("Сначала авторизуйся: /start")
        return ConversationHandler.END

    employees = await client.get_employees()
    context.user_data["employees"] = {e["employee_id"]: e for e in employees}

    await update.message.reply_text(
        "📋 История по сотруднику.\nВыбери сотрудника:",
        reply_markup=employees_keyboard(employees),
    )
    return HISTORY_SELECT_EMPLOYEE


async def history_select_employee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    employee_id = query.data.replace("emp_", "")
    employees = context.user_data.get("employees", {})
    employee = employees.get(employee_id)

    client = get_client(update)
    feedbacks = await client.get_feedback_history(employee_id)

    if not feedbacks:
        await query.edit_message_text(
            f"📋 История: {employee['full_name']}\n\nКомментариев нет.",
            reply_markup=None,
        )
        return ConversationHandler.END

    msg = _format_history(employee["full_name"], feedbacks[:10])
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=None)
    return ConversationHandler.END


def _format_history(name: str, feedbacks: list[dict]) -> str:
    lines = [f"📋 *История: {name}*\n"]

    for fb in feedbacks:
        date_str = fb.get("feedback_date", "")[:10]
        status = STATUS_LABELS.get(fb.get("status", ""), fb.get("status", ""))
        text = fb.get("original_text", "")
        if len(text) > 150:
            text = text[:150] + "…"

        lines.append(f"━━━━━━━━━━")
        lines.append(f"📅 {date_str} | {status}")
        lines.append(f"_«{text}»_")

        mappings = fb.get("mappings", [])
        if mappings:
            for m in mappings[:3]:
                rating = m.get("confirmed_rating") or m.get("suggested_rating") or "?"
                emoji = RATING_EMOJI.get(rating, "")
                criterion = m.get("criterion_name", "?")
                lines.append(f"  • {criterion} — {emoji}")
        lines.append("")

    if len(lines) > 50:
        lines.append("_Показаны последние 10 комментариев. Полная история — в веб-кабинете._")

    return "\n".join(lines)
