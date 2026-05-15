from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from app.bot.states import AWAITING_EMAIL
from app.bot.utils import main_menu_keyboard
from app.bot.api_client import BotApiClient
from app.config import settings


# Хранилище токенов (telegram_id → token)
_user_tokens: dict[int, str] = {}


async def get_or_require_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """Возвращает JWT токен или None если не авторизован (и запускает auth flow)."""
    tg_id = update.effective_user.id
    if tg_id in _user_tokens:
        return _user_tokens[tg_id]

    # Пробуем получить токен через telegram_id
    client = BotApiClient("")
    auth_data = await client.auth_by_telegram(tg_id)
    if auth_data:
        _user_tokens[tg_id] = auth_data["access_token"]
        return auth_data["access_token"]

    return None


def get_client(update: Update) -> BotApiClient | None:
    tg_id = update.effective_user.id
    token = _user_tokens.get(tg_id)
    if not token:
        return None
    return BotApiClient(token)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg_id = update.effective_user.id
    token = await get_or_require_auth(update, context)

    if token:
        client = BotApiClient(token)
        # Проверяем валидность токена по запросу к /employees
        try:
            await client.get_employees()
        except Exception:
            _user_tokens.pop(tg_id, None)
            token = None

    if token:
        await update.message.reply_text(
            f"👋 Привет, {update.effective_user.first_name}!\n\n"
            "Выбери действие:",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "👋 Добро пожаловать в Feedback Assistant!\n\n"
        "Этот бот помогает фиксировать наблюдения по сотрудникам и "
        "готовить evidence-based summary для performance review.\n\n"
        "Для начала работы напиши свой корпоративный email:"
    )
    return AWAITING_EMAIL


async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip().lower()
    tg_id = update.effective_user.id

    if "@" not in email:
        await update.message.reply_text("Пожалуйста, введи корректный email:")
        return AWAITING_EMAIL

    client = BotApiClient("")
    auth_data = await client.link_telegram(tg_id, email)

    if auth_data:
        _user_tokens[tg_id] = auth_data["access_token"]
        await update.message.reply_text(
            f"✅ Готово! Привязал Telegram к аккаунту {auth_data['full_name']}.\n\n"
            "Теперь ты можешь пользоваться ботом:",
            reply_markup=main_menu_keyboard(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "❌ Email не найден в системе.\n"
        "Обратись к администратору, чтобы тебя добавили.\n\n"
        "Попробуй снова:"
    )
    return AWAITING_EMAIL


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Открыть веб-кабинет" in text:
        await update.message.reply_text(
            f"🌐 Веб-кабинет доступен по адресу:\n{settings.app_url}",
            reply_markup=main_menu_keyboard(),
        )
