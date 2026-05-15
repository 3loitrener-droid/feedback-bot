from __future__ import annotations
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.bot.states import (
    FEEDBACK_SELECT_EMPLOYEE, FEEDBACK_INPUT_TEXT, FEEDBACK_SELECT_MODE,
    FEEDBACK_SELECT_CRITERIA, FEEDBACK_RATE_CRITERION, FEEDBACK_CONFIRM_AUTO,
    FEEDBACK_EDIT_MAPPING,
)
from app.bot.utils import employees_keyboard, criteria_keyboard, rating_keyboard, confirm_keyboard, format_mappings_preview, main_menu_keyboard
from app.bot.handlers.start import get_client, _user_tokens
from app.bot.api_client import BotApiClient


def _get_client_from_context(context: ContextTypes.DEFAULT_TYPE) -> BotApiClient | None:
    """Получить клиент из сохранённого tg_id в user_data (для helper-функций без update)."""
    tg_id = context.user_data.get("tg_id")
    if tg_id is None:
        return None
    token = _user_tokens.get(tg_id)
    if not token:
        return None
    return BotApiClient(token)


async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    client = get_client(update)
    if not client:
        await update.message.reply_text("Сначала авторизуйся: /start")
        return ConversationHandler.END

    # Сохраняем tg_id для helper-функций
    context.user_data["tg_id"] = update.effective_user.id

    try:
        employees = await client.get_employees()
    except Exception:
        await update.message.reply_text("Ошибка загрузки команды. Попробуй позже.")
        return ConversationHandler.END

    if not employees:
        await update.message.reply_text("Твоя команда пуста. Обратись к администратору.")
        return ConversationHandler.END

    context.user_data["employees"] = {e["employee_id"]: e for e in employees}

    await update.message.reply_text(
        "👤 По кому хочешь оставить фидбэк?\n\nВыбери сотрудника:",
        reply_markup=employees_keyboard(employees),
    )
    return FEEDBACK_SELECT_EMPLOYEE


async def select_employee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    employee_id = query.data.replace("emp_", "")
    employees = context.user_data.get("employees", {})
    employee = employees.get(employee_id)
    if not employee:
        await query.edit_message_text("Сотрудник не найден.")
        return ConversationHandler.END

    context.user_data["selected_employee"] = employee
    context.user_data["selected_criteria"] = []
    context.user_data["pending_ratings"] = {}

    await query.edit_message_text(
        f"✅ Выбран: {employee['full_name']}\n\n"
        "✍️ Напиши наблюдение.\n\n"
        "Лучше фиксировать конкретику:\n"
        "— что произошло\n"
        "— что сделал / не сделал сотрудник\n"
        "— как это повлияло на результат"
    )
    return FEEDBACK_INPUT_TEXT


async def input_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("Комментарий не может быть пустым. Напиши снова:")
        return FEEDBACK_INPUT_TEXT

    context.user_data["feedback_text"] = text
    employee = context.user_data["selected_employee"]

    await update.message.reply_text(
        f"📝 Комментарий принят.\n\n"
        f"Как размечаем по матрице?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✨ Определить автоматически", callback_data="mode_auto")],
            [InlineKeyboardButton("📋 Выбрать критерий вручную", callback_data="mode_manual")],
            [InlineKeyboardButton("🚫 Оставить без критерия", callback_data="mode_none")],
        ]),
    )
    return FEEDBACK_SELECT_MODE


async def select_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    mode = query.data.replace("mode_", "")

    if mode == "none":
        await _save_feedback_no_criterion(update, context, query)
        return ConversationHandler.END

    if mode == "auto":
        await query.edit_message_text("🔍 Анализирую... ⏳")
        client = get_client(update)
        employee = context.user_data["selected_employee"]
        text = context.user_data["feedback_text"]

        try:
            result = await client.analyze_feedback(text, employee)
        except Exception as e:
            await query.edit_message_text(
                f"⚠️ Ошибка автоматического анализа: {str(e)[:100]}\n\n"
                "Переключаюсь на ручной выбор.",
                reply_markup=None,
            )
            mode = "manual"
        else:
            context.user_data["llm_mappings"] = result.get("mappings", [])
            needs_clarification = result.get("needs_clarification", False)

            if needs_clarification:
                clarification = result.get("clarification_request", "")
                await query.edit_message_text(
                    f"🤔 Комментарий слишком общий.\n\n{clarification}\n\n"
                    "Хочешь добавить конкретику или оставить без критерия?",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🚫 Оставить без критерия", callback_data="mode_none")],
                    ]),
                )
                return FEEDBACK_SELECT_MODE

            mappings = result.get("mappings", [])
            if not mappings:
                await query.edit_message_text(
                    "🤷 Не удалось определить критерии автоматически.\n"
                    "Выбери вручную или оставь без критерия.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📋 Выбрать вручную", callback_data="mode_manual")],
                        [InlineKeyboardButton("🚫 Без критерия", callback_data="mode_none")],
                    ]),
                )
                return FEEDBACK_SELECT_MODE

            preview = format_mappings_preview(mappings)
            await query.edit_message_text(
                f"🔎 Разбил комментарий на {len(mappings)} критерия(ев):\n\n"
                f"{preview}\n\n"
                "Подтверди или отредактируй:",
                reply_markup=confirm_keyboard(),
            )
            return FEEDBACK_CONFIRM_AUTO

    if mode == "manual":
        client = get_client(update)
        try:
            criteria = await client.get_criteria()
        except Exception:
            await query.edit_message_text("Ошибка загрузки критериев.")
            return ConversationHandler.END

        context.user_data["criteria"] = {c["criterion_id"]: c for c in criteria}
        context.user_data["selected_criteria"] = []

        await query.edit_message_text(
            "📋 Выбери критерий (можно несколько).\nНажми нужные и затем «Готово»:",
            reply_markup=criteria_keyboard(criteria),
        )
        return FEEDBACK_SELECT_CRITERIA

    return ConversationHandler.END


async def select_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "crit_none":
        await _save_feedback_no_criterion(update, context, query)
        return ConversationHandler.END

    if data == "crit_auto":
        # Переключаемся в авто-режим
        await query.edit_message_text("🔍 Анализирую... ⏳")
        client = get_client(update)
        employee = context.user_data["selected_employee"]
        text = context.user_data["feedback_text"]
        try:
            result = await client.analyze_feedback(text, employee)
            context.user_data["llm_mappings"] = result.get("mappings", [])
            mappings = result.get("mappings", [])
            if mappings:
                preview = format_mappings_preview(mappings)
                await query.edit_message_text(
                    f"🔎 Разбил на {len(mappings)} критерия(ев):\n\n{preview}\n\nПодтверди:",
                    reply_markup=confirm_keyboard(),
                )
                return FEEDBACK_CONFIRM_AUTO
            else:
                await query.edit_message_text("Критерии не определены. Выбери вручную.")
        except Exception:
            await query.edit_message_text("Ошибка анализа. Попробуй снова.")
        return FEEDBACK_SELECT_CRITERIA

    if data == "crit_done":
        selected = context.user_data.get("selected_criteria", [])
        if not selected:
            await query.answer("Выбери хотя бы один критерий", show_alert=True)
            return FEEDBACK_SELECT_CRITERIA

        context.user_data["rating_queue"] = list(selected)
        context.user_data["collected_ratings"] = {}
        return await _ask_next_rating(query, context)

    # Тоггл критерия
    criterion_id = data.replace("crit_", "")
    selected = context.user_data.get("selected_criteria", [])
    criteria = context.user_data.get("criteria", {})

    if criterion_id in selected:
        selected.remove(criterion_id)
    else:
        selected.append(criterion_id)
    context.user_data["selected_criteria"] = selected

    await query.edit_message_reply_markup(
        reply_markup=criteria_keyboard(list(criteria.values()), selected)
    )
    return FEEDBACK_SELECT_CRITERIA


async def rate_criterion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # format: rate_{idx}_{rating}
    parts = query.data.split("_", 2)
    idx = int(parts[1])
    rating = parts[2]

    queue = context.user_data.get("rating_queue", [])
    ratings = context.user_data.get("collected_ratings", {})
    ratings[queue[idx]] = rating
    context.user_data["collected_ratings"] = ratings

    if idx + 1 < len(queue):
        # Следующий критерий
        context.user_data["current_rating_idx"] = idx + 1
        return await _ask_next_rating(query, context, idx + 1)

    # Все оценки собраны — сохраняем
    return await _save_feedback_with_manual_ratings(update, context, query)


async def confirm_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    mappings = context.user_data.get("llm_mappings", [])

    if action == "confirm_all":
        await _save_feedback_confirmed(update, context, query, mappings)
        return ConversationHandler.END

    if action == "confirm_none":
        await _save_feedback_no_criterion(update, context, query)
        return ConversationHandler.END

    if action == "confirm_delete":
        context.user_data.clear()
        await query.edit_message_text("🗑 Запись удалена.", reply_markup=None)
        return ConversationHandler.END

    if action == "confirm_edit":
        # Показываем список для редактирования
        buttons = []
        for i, m in enumerate(mappings):
            name = m["criterion_name"][:20]
            rating = m.get("suggested_rating", "?")[:4]
            buttons.append([
                InlineKeyboardButton(f"✏️ {i+1}. {name}", callback_data=f"editcrit_{i}"),
                InlineKeyboardButton(f"🗑", callback_data=f"delmap_{i}"),
            ])
        buttons.append([InlineKeyboardButton("✅ Сохранить как есть", callback_data="confirm_all")])
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
        return FEEDBACK_EDIT_MAPPING

    return FEEDBACK_CONFIRM_AUTO


async def edit_mapping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    mappings = context.user_data.get("llm_mappings", [])

    if data.startswith("delmap_"):
        idx = int(data.replace("delmap_", ""))
        if 0 <= idx < len(mappings):
            mappings.pop(idx)
        context.user_data["llm_mappings"] = mappings

        if not mappings:
            await _save_feedback_no_criterion(update, context, query)
            return ConversationHandler.END

        preview = format_mappings_preview(mappings)
        await query.edit_message_text(
            f"Обновлённые связки ({len(mappings)}):\n\n{preview}",
            reply_markup=confirm_keyboard(),
        )
        return FEEDBACK_CONFIRM_AUTO

    if data.startswith("editrate_"):
        parts = data.split("_")
        idx = int(parts[1])
        rating = "_".join(parts[2:])
        if 0 <= idx < len(mappings):
            mappings[idx]["suggested_rating"] = rating
        context.user_data["llm_mappings"] = mappings

        preview = format_mappings_preview(mappings)
        await query.edit_message_text(
            f"✅ Оценка обновлена.\n\n{preview}",
            reply_markup=confirm_keyboard(),
        )
        return FEEDBACK_CONFIRM_AUTO

    if data.startswith("editcrit_"):
        idx = int(data.replace("editcrit_", ""))
        context.user_data["editing_mapping_idx"] = idx
        m = mappings[idx]
        await query.edit_message_text(
            f"Редактирую связку {idx+1}:\n"
            f"Критерий: {m['criterion_name']}\n"
            f"Оценка: {m.get('suggested_rating', '?')}\n\n"
            "Выбери новую оценку:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⬇️ Below", callback_data=f"editrate_{idx}_Below expectations"),
                    InlineKeyboardButton("➡️ Meet", callback_data=f"editrate_{idx}_Meet expectations"),
                    InlineKeyboardButton("⬆️ Exceeds", callback_data=f"editrate_{idx}_Exceeds expectations"),
                ],
                [InlineKeyboardButton("↩️ Назад", callback_data="confirm_edit")],
            ]),
        )
        return FEEDBACK_EDIT_MAPPING

    return FEEDBACK_EDIT_MAPPING


# Helpers

async def _ask_next_rating(query, context: ContextTypes.DEFAULT_TYPE, idx: int = 0) -> int:
    queue = context.user_data.get("rating_queue", [])
    criteria = context.user_data.get("criteria", {})
    if idx >= len(queue):
        return await _save_feedback_with_manual_ratings(None, context, query)  # update=None handled below

    criterion_id = queue[idx]
    criterion = criteria.get(criterion_id, {})
    name = criterion.get("criterion_name", criterion_id)

    context.user_data["current_rating_idx"] = idx
    await query.edit_message_text(
        f"Оценка по критерию «{name}» ({idx+1}/{len(queue)}):",
        reply_markup=rating_keyboard(name, idx),
    )
    return FEEDBACK_RATE_CRITERION


async def _save_feedback_no_criterion(update, context, query=None):
    client = get_client(update) if update is not None else _get_client_from_context(context)
    employee = context.user_data["selected_employee"]
    text = context.user_data["feedback_text"]

    try:
        await client.create_feedback({
            "employee_id": employee["employee_id"],
            "original_text": text,
            "source": "telegram",
            "mappings": [],
        })
        msg = (
            f"✅ Комментарий сохранён без критерия.\n\n"
            f"👤 {employee['full_name']}\n"
            "Статус: ⚠️ Требует разметки\n\n"
            "Ты сможешь добавить критерий позже в веб-кабинете или в истории."
        )
    except Exception as e:
        msg = f"❌ Ошибка сохранения: {str(e)[:100]}"

    context.user_data.clear()
    if query:
        await query.edit_message_text(msg, reply_markup=None)
    else:
        await update.message.reply_text(msg)


async def _save_feedback_confirmed(update, context, query, mappings: list[dict]):
    client = get_client(update) if update is not None else _get_client_from_context(context)
    employee = context.user_data["selected_employee"]
    text = context.user_data["feedback_text"]

    # Нам нужны criterion_id для mappings
    # Делаем запрос к критериям для поиска по имени
    try:
        all_criteria = await client.get_criteria()
        name_to_id = {c["criterion_name"]: c["criterion_id"] for c in all_criteria}

        mappings_payload = []
        for m in mappings:
            cid = name_to_id.get(m["criterion_name"])
            if cid:
                mappings_payload.append({
                    "criterion_id": cid,
                    "original_fragment": m.get("original_fragment"),
                    "suggested_rating": m.get("suggested_rating"),
                    "confirmed_rating": m.get("suggested_rating"),
                    "llm_explanation": m.get("explanation"),
                    "manager_confirmed": True,
                })

        await client.create_feedback({
            "employee_id": employee["employee_id"],
            "original_text": text,
            "source": "telegram",
            "mappings": mappings_payload,
        })

        lines = [f"• {m['criterion_name']} — {m.get('suggested_rating', '?')[:6]} ✓" for m in mappings]
        msg = (
            f"✅ Фидбэк сохранён.\n\n"
            f"👤 {employee['full_name']}\n\n"
            "Исходный комментарий сохранён точь-в-точь.\n"
            f"Разбит на {len(mappings)} критерия(ев):\n" +
            "\n".join(lines)
        )
    except Exception as e:
        msg = f"❌ Ошибка сохранения: {str(e)[:100]}"

    context.user_data.clear()
    await query.edit_message_text(msg, reply_markup=None)


async def _save_feedback_with_manual_ratings(update, context, query):
    client = get_client(update) if update is not None else _get_client_from_context(context)
    employee = context.user_data["selected_employee"]
    text = context.user_data["feedback_text"]
    queue = context.user_data.get("rating_queue", [])
    ratings = context.user_data.get("collected_ratings", {})
    criteria = context.user_data.get("criteria", {})

    try:
        mappings_payload = []
        lines = []
        for cid in queue:
            rating = ratings.get(cid)
            if rating:
                mappings_payload.append({
                    "criterion_id": cid,
                    "confirmed_rating": rating,
                    "suggested_rating": rating,
                    "manager_confirmed": True,
                })
                name = criteria.get(cid, {}).get("criterion_name", cid)
                lines.append(f"• {name} — {rating[:6]} ✓")

        await client.create_feedback({
            "employee_id": employee["employee_id"],
            "original_text": text,
            "source": "telegram",
            "mappings": mappings_payload,
        })

        msg = (
            f"✅ Фидбэк сохранён.\n\n"
            f"👤 {employee['full_name']}\n\n" +
            "\n".join(lines)
        )
    except Exception as e:
        msg = f"❌ Ошибка сохранения: {str(e)[:100]}"

    context.user_data.clear()
    if query:
        await query.edit_message_text(msg, reply_markup=None)
    elif update and update.message:
        await update.message.reply_text(msg)
    return ConversationHandler.END
