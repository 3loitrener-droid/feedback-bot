from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.bot.states import PREP_1_1_EMPLOYEE, PREP_PR_EMPLOYEE, PREP_PR_PERIOD
from app.bot.utils import employees_keyboard, period_keyboard, RATING_EMOJI
from app.bot.handlers.start import get_client


async def prep_1_1_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    client = get_client(update)
    if not client:
        await update.message.reply_text("Сначала авторизуйся: /start")
        return ConversationHandler.END

    employees = await client.get_employees()
    context.user_data["employees"] = {e["employee_id"]: e for e in employees}

    await update.message.reply_text(
        "🗣 Подготовка к 1:1.\nВыбери сотрудника:",
        reply_markup=employees_keyboard(employees),
    )
    return PREP_1_1_EMPLOYEE


async def prep_1_1_employee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    employee_id = query.data.replace("emp_", "")
    employees = context.user_data.get("employees", {})
    employee = employees.get(employee_id)

    client = get_client(update)
    feedbacks = await client.get_feedback_history(employee_id)

    msg = _format_1_1_prep(employee["full_name"], feedbacks)
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=None)
    return ConversationHandler.END


def _format_1_1_prep(name: str, feedbacks: list[dict]) -> str:
    if not feedbacks:
        return (
            f"🗣 *Подготовка к 1:1: {name}*\n\n"
            "Нет зафиксированных комментариев.\n"
            "Добавь наблюдения через «📝 Оставить фидбэк» перед встречей."
        )

    # Группируем по критериям для поиска паттернов
    criterion_counts: dict[str, int] = {}
    criterion_evidence: dict[str, list[str]] = {}
    below_criteria: list[str] = []

    for fb in feedbacks:
        for m in fb.get("mappings", []):
            cname = m.get("criterion_name", "")
            rating = m.get("confirmed_rating") or m.get("suggested_rating") or ""
            criterion_counts[cname] = criterion_counts.get(cname, 0) + 1
            criterion_evidence.setdefault(cname, []).append(fb["original_text"][:100])
            if rating == "Below expectations" and cname not in below_criteria:
                below_criteria.append(cname)

    top_topics = sorted(criterion_counts.items(), key=lambda x: -x[1])[:3]

    lines = [f"🗣 *Подготовка к 1:1: {name}*\n"]
    lines.append("*Темы для обсуждения:*\n")

    questions = {
        "Предсказуемость execution": "Что помогло бы тебе лучше управлять сроками и рисками?",
        "Работа со стейкхолдерами": "Как ты готовишься к ключевым встречам с LT?",
        "Артефакты": "Какие артефакты ты считаешь наиболее важными для твоей роли?",
        "Сколачивание сильной команды": "Что изменилось в команде за последнее время? Как это произошло?",
        "Ответственность": "Как ты расставляешь приоритеты, когда берёшь на себя ответственность?",
    }

    for i, (criterion, count) in enumerate(top_topics, 1):
        evidence = criterion_evidence.get(criterion, [])
        quote = f"_«{evidence[0][:100]}»_" if evidence else ""
        question = questions.get(criterion, "Как ты оцениваешь свой прогресс по этому направлению?")
        lines.append(f"*{i}. {criterion}*")
        if quote:
            lines.append(f"Evidence: {quote}")
        lines.append(f"Вопрос: {question}\n")

    if below_criteria:
        lines.append("*⚠️ Зоны для развития:*")
        for c in below_criteria[:2]:
            lines.append(f"• {c}")
        lines.append("")

    lines.append("_Важно: веди разговор конструктивно, фокусируясь на поведении, а не личных качествах._")
    return "\n".join(lines)


async def prep_pr_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    client = get_client(update)
    if not client:
        await update.message.reply_text("Сначала авторизуйся: /start")
        return ConversationHandler.END

    employees = await client.get_employees()
    context.user_data["employees"] = {e["employee_id"]: e for e in employees}

    await update.message.reply_text(
        "📄 Performance Review.\nВыбери сотрудника:",
        reply_markup=employees_keyboard(employees),
    )
    return PREP_PR_EMPLOYEE


async def prep_pr_employee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    employee_id = query.data.replace("emp_", "")
    employees = context.user_data.get("employees", {})
    context.user_data["pr_employee"] = employees.get(employee_id)

    await query.edit_message_text(
        f"Выбран: {context.user_data['pr_employee']['full_name']}\n\nВыбери период:",
        reply_markup=period_keyboard(),
    )
    return PREP_PR_PERIOD


async def prep_pr_period(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    employee = context.user_data["pr_employee"]
    client = get_client(update)

    periods = await client.get_periods()
    period = next((p for p in periods if p["is_active"]), periods[0] if periods else None)
    if not period:
        await query.edit_message_text("Периоды не найдены.")
        return ConversationHandler.END

    summary = await client.get_summary(employee["employee_id"], period["period_id"])

    if not summary:
        await query.edit_message_text(
            f"⏳ Формирую Performance Review по {employee['full_name']}...\n\nЭто займёт ~15 сек."
        )
        try:
            await client.generate_summary(employee["employee_id"], period["period_id"])
            summary = await client.get_summary(employee["employee_id"], period["period_id"])
        except Exception:
            pass

    if not summary:
        feedbacks = await client.get_feedback_history(employee["employee_id"], period["period_id"])
        msg = _format_pr_basic(employee["full_name"], period["period_name"], feedbacks)
    else:
        msg = _format_pr_full(employee["full_name"], period["period_name"], summary)

    try:
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=None)
    except Exception:
        clean = msg.replace("*", "").replace("_", "").replace("`", "")
        try:
            await query.edit_message_text(clean, reply_markup=None)
        except Exception:
            pass
    return ConversationHandler.END


def _format_pr_full(name: str, period_name: str, summary: dict) -> str:
    recommendation = summary.get("rating_recommendation", "insufficient_data")
    rating_emoji = RATING_EMOJI.get(recommendation, "⚪")

    lines = [f"📝 *Performance Review: {name} | {period_name}*\n"]
    lines.append(f"*Рекомендация системы:* {rating_emoji} {recommendation}\n")

    breakdown = summary.get("criterion_breakdown") or []
    if breakdown:
        lines.append("*Оценки по критериям:*")
        for c in breakdown[:6]:
            b, m, e = c.get("below_count", 0), c.get("meet_count", 0), c.get("exceeds_count", 0)
            lines.append(f"• {c['criterion_name']}: 🔴×{b} 🟡×{m} 🟢×{e}")
        lines.append("")

    strengths = summary.get("strengths") or []
    if strengths:
        lines.append("*Сильные зоны:*")
        for s in strengths[:2]:
            lines.append(f"✅ {s['criterion_name']}")
            for q in s.get("evidence_quotes", [])[:1]:
                lines.append(f"  _«{q[:100]}»_")
        lines.append("")

    growth = summary.get("growth_areas") or []
    if growth:
        lines.append("*Зоны роста:*")
        for g in growth[:2]:
            lines.append(f"⚠️ {g['criterion_name']}")
            for q in g.get("evidence_quotes", [])[:1]:
                lines.append(f"  _«{q[:100]}»_")
        lines.append("")

    args_for = summary.get("arguments_for") or []
    if args_for:
        lines.append("*Аргументы за:*")
        for a in args_for[:2]:
            lines.append(f"+ {a[:100]}")
        lines.append("")

    args_against = summary.get("arguments_against") or []
    if args_against:
        lines.append("*Риски:*")
        for a in args_against[:2]:
            lines.append(f"- {a[:100]}")
        lines.append("")

    needs = summary.get("needs_attention") or []
    if needs:
        lines.append(f"*⚠️ Требует проверки:* {len(needs)} комментарий(ев) без разметки")
        lines.append("")

    lines.append("_Полный отчёт с экспортом — в веб-кабинете._")
    return "\n".join(lines)


def _format_pr_basic(name: str, period_name: str, feedbacks: list[dict]) -> str:
    total = len(feedbacks)
    lines = [
        f"📝 *Performance Review: {name} | {period_name}*\n",
        f"Всего комментариев: {total}\n",
        "_Summary ещё не сгенерировано. Открой веб-кабинет для полного отчёта._",
    ]
    return "\n".join(lines)
