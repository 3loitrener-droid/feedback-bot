import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters,
)
from app.config import settings
from app.bot.states import (
    FEEDBACK_SELECT_EMPLOYEE, FEEDBACK_INPUT_TEXT, FEEDBACK_SELECT_MODE,
    FEEDBACK_SELECT_CRITERIA, FEEDBACK_RATE_CRITERION, FEEDBACK_CONFIRM_AUTO,
    FEEDBACK_EDIT_MAPPING,
    SUMMARY_SELECT_EMPLOYEE, SUMMARY_SELECT_PERIOD,
    HISTORY_SELECT_EMPLOYEE, PREP_1_1_EMPLOYEE,
    PREP_PR_EMPLOYEE, PREP_PR_PERIOD, AWAITING_EMAIL,
)
from app.bot.handlers.start import start_handler, handle_email, handle_main_menu
from app.bot.handlers.feedback import (
    feedback_start, select_employee, input_text, select_mode,
    select_criteria, rate_criterion, confirm_auto, edit_mapping,
)
from app.bot.handlers.summary import (
    summary_start, summary_select_employee, summary_select_period,
)
from app.bot.handlers.history import (
    history_start, history_select_employee,
)
from app.bot.handlers.review import (
    prep_1_1_start, prep_1_1_employee,
    prep_pr_start, prep_pr_employee, prep_pr_period,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


def build_app() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()

    # ConversationHandler для фидбэка
    feedback_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Оставить фидбэк$"), feedback_start)],
        states={
            FEEDBACK_SELECT_EMPLOYEE: [CallbackQueryHandler(select_employee, pattern="^emp_")],
            FEEDBACK_INPUT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_text)],
            FEEDBACK_SELECT_MODE: [CallbackQueryHandler(select_mode, pattern="^mode_")],
            FEEDBACK_SELECT_CRITERIA: [CallbackQueryHandler(select_criteria, pattern="^crit_")],
            FEEDBACK_RATE_CRITERION: [CallbackQueryHandler(rate_criterion, pattern="^rate_")],
            FEEDBACK_CONFIRM_AUTO: [CallbackQueryHandler(confirm_auto, pattern="^confirm_")],
            FEEDBACK_EDIT_MAPPING: [CallbackQueryHandler(edit_mapping, pattern="^(editcrit_|editrate_|delmap_)")],
        },
        fallbacks=[CommandHandler("cancel", start_handler), MessageHandler(filters.Regex("^🔙"), start_handler)],
        per_user=True,
        per_chat=True,
    )

    # ConversationHandler для summary
    summary_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📊 Посмотреть summary$"), summary_start)],
        states={
            SUMMARY_SELECT_EMPLOYEE: [CallbackQueryHandler(summary_select_employee, pattern="^emp_")],
            SUMMARY_SELECT_PERIOD: [CallbackQueryHandler(summary_select_period, pattern="^period_")],
        },
        fallbacks=[CommandHandler("cancel", start_handler)],
        per_user=True, per_chat=True,
    )

    # История
    history_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📋 История$"), history_start)],
        states={
            HISTORY_SELECT_EMPLOYEE: [CallbackQueryHandler(history_select_employee, pattern="^emp_")],
        },
        fallbacks=[CommandHandler("cancel", start_handler)],
        per_user=True, per_chat=True,
    )

    # 1:1
    prep_1_1_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗣 Подготовиться к 1:1$"), prep_1_1_start)],
        states={
            PREP_1_1_EMPLOYEE: [CallbackQueryHandler(prep_1_1_employee, pattern="^emp_")],
        },
        fallbacks=[CommandHandler("cancel", start_handler)],
        per_user=True, per_chat=True,
    )

    # Performance Review
    prep_pr_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📄 Performance Review$"), prep_pr_start)],
        states={
            PREP_PR_EMPLOYEE: [CallbackQueryHandler(prep_pr_employee, pattern="^emp_")],
            PREP_PR_PERIOD: [CallbackQueryHandler(prep_pr_period, pattern="^period_")],
        },
        fallbacks=[CommandHandler("cancel", start_handler)],
        per_user=True, per_chat=True,
    )

    # Auth flow
    auth_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start_handler)],
        states={
            AWAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
        },
        fallbacks=[CommandHandler("cancel", start_handler)],
        per_user=True, per_chat=True,
    )

    app.add_handler(auth_conv)
    app.add_handler(feedback_conv)
    app.add_handler(summary_conv)
    app.add_handler(history_conv)
    app.add_handler(prep_1_1_conv)
    app.add_handler(prep_pr_conv)

    # Веб-кабинет и прочие кнопки главного меню
    app.add_handler(MessageHandler(filters.Regex("^🌐 Открыть веб-кабинет$"), handle_main_menu))

    return app


def main():
    app = build_app()
    log.info("Feedback Assistant Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
