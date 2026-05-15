from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

RATING_LABELS = {
    "Below expectations": "⬇️ Below",
    "Meet expectations": "➡️ Meet",
    "Exceeds expectations": "⬆️ Exceeds",
}

RATING_EMOJI = {
    "Below expectations": "🔴",
    "Meet expectations": "🟡",
    "Exceeds expectations": "🟢",
}

STATUS_LABELS = {
    "confirmed": "✅ Подтверждён",
    "draft": "📝 Черновик",
    "no_criterion": "⚠️ Без критерия",
    "needs_review": "🔍 Требует проверки",
}


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton("📝 Оставить фидбэк")],
        [KeyboardButton("📊 Посмотреть summary"), KeyboardButton("📋 История")],
        [KeyboardButton("🗣 Подготовиться к 1:1"), KeyboardButton("📄 Performance Review")],
        [KeyboardButton("🌐 Открыть веб-кабинет")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def employees_keyboard(employees: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for emp in employees:
        buttons.append([InlineKeyboardButton(emp["full_name"], callback_data=f"emp_{emp['employee_id']}")])
    return InlineKeyboardMarkup(buttons)


def criteria_keyboard(criteria: list[dict], selected: list[str] | None = None) -> InlineKeyboardMarkup:
    selected = selected or []
    buttons = []
    row = []
    for i, c in enumerate(criteria):
        cid = str(c["criterion_id"])
        mark = "✓ " if cid in selected else ""
        name = c["criterion_name"]
        short = name[:22] + "…" if len(name) > 22 else name
        row.append(InlineKeyboardButton(f"{mark}{short}", callback_data=f"crit_{cid}"))
        if len(row) == 2 or i == len(criteria) - 1:
            buttons.append(row)
            row = []

    buttons.append([
        InlineKeyboardButton("✨ Определить автоматически", callback_data="crit_auto"),
    ])
    buttons.append([
        InlineKeyboardButton("🚫 Без критерия", callback_data="crit_none"),
    ])
    if selected:
        buttons.append([InlineKeyboardButton(f"✅ Готово ({len(selected)} выбрано)", callback_data="crit_done")])
    return InlineKeyboardMarkup(buttons)


def rating_keyboard(criterion_name: str, mapping_idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬇️ Below", callback_data=f"rate_{mapping_idx}_Below expectations"),
            InlineKeyboardButton("➡️ Meet", callback_data=f"rate_{mapping_idx}_Meet expectations"),
            InlineKeyboardButton("⬆️ Exceeds", callback_data=f"rate_{mapping_idx}_Exceeds expectations"),
        ]
    ])


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Подтвердить всё", callback_data="confirm_all")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="confirm_edit")],
        [InlineKeyboardButton("🚫 Оставить без критерия", callback_data="confirm_none")],
        [InlineKeyboardButton("🗑 Удалить запись", callback_data="confirm_delete")],
    ])


def period_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Эта неделя", callback_data="period_week")],
        [InlineKeyboardButton("Этот месяц", callback_data="period_month")],
        [InlineKeyboardButton("Этот квартал", callback_data="period_quarter")],
        [InlineKeyboardButton("Это полугодие", callback_data="period_half")],
    ])


def format_rating(rating: str | None) -> str:
    if not rating:
        return "—"
    emoji = RATING_EMOJI.get(rating, "")
    return f"{emoji} {rating}"


def format_mappings_preview(mappings: list[dict]) -> str:
    if not mappings:
        return "Нет связок"
    lines = []
    for i, m in enumerate(mappings, 1):
        rating = format_rating(m.get("suggested_rating"))
        fragment = m.get("original_fragment", "")
        if len(fragment) > 60:
            fragment = fragment[:60] + "…"
        lines.append(
            f"{i}. {m.get('criterion_name', '?')}\n"
            f"   «{fragment}»\n"
            f"   Оценка: {rating}\n"
            f"   {m.get('explanation', '')}"
        )
    return "\n\n".join(lines)
