from telegram.ext import ConversationHandler

# Состояния для сценария "Оставить фидбэк"
(
    FEEDBACK_SELECT_EMPLOYEE,
    FEEDBACK_INPUT_TEXT,
    FEEDBACK_SELECT_MODE,
    FEEDBACK_SELECT_CRITERIA,
    FEEDBACK_RATE_CRITERION,
    FEEDBACK_CONFIRM_AUTO,
    FEEDBACK_EDIT_MAPPING,
) = range(7)

# Состояния для сценария "Summary"
(
    SUMMARY_SELECT_EMPLOYEE,
    SUMMARY_SELECT_PERIOD,
) = range(7, 9)

# Состояния для "История"
(
    HISTORY_SELECT_EMPLOYEE,
    HISTORY_VIEW,
) = range(9, 11)

# Состояния для "1:1"
(
    PREP_1_1_EMPLOYEE,
) = range(11, 12)

# Состояния для "Performance Review"
(
    PREP_PR_EMPLOYEE,
    PREP_PR_PERIOD,
) = range(12, 14)

# Авторизация
AWAITING_EMAIL = 14
