import logging
import os
from dotenv import load_dotenv

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

# Загрузка переменных окружения из .env файла
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определяем состояния разговора
START_CHOICE, GET_NAME, GET_PHONE, CONFIRM_PHONE, CHOOSE_SLOT, CONFIRMATION = range(6)

# --- Функции обработчики ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает разговор и спрашивает пользователя, хочет ли он записаться."""
    keyboard = [
        [InlineKeyboardButton("Да, хочу!", callback_data="signup_yes")],
        [InlineKeyboardButton("Расскажи подробнее", callback_data="details")],
        [InlineKeyboardButton("Нет, спасибо", callback_data="signup_no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Привет! 👋 Хочешь попробовать танго? У нас есть бесплатный урок для новичков — "
        "идеальная возможность почувствовать ритм и страсть этого танца! Хочешь записаться?",
        reply_markup=reply_markup,
    )
    return START_CHOICE

async def start_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор пользователя на стартовом сообщении."""
    query = update.callback_query
    await query.answer() # Отвечаем на коллбек, чтобы кнопка перестала "грузиться"

    if query.data == "signup_yes":
        await query.edit_message_text(text="Отлично, давай запишем тебя! Как тебя зовут?")
        return GET_NAME
    elif query.data == "details":
        keyboard = [
            [InlineKeyboardButton("Да, записаться!", callback_data="signup_yes")],
            [InlineKeyboardButton("Нет, спасибо", callback_data="signup_no")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="Это 60-минутный урок, где ты познакомишься с основами танго, попробуешь первые шаги "
                 "и почувствуешь атмосферу. Никакого опыта не нужно, просто приходи в удобной одежде! "
                 "Готов записаться?",
            reply_markup=reply_markup,
        )
        return START_CHOICE # Остаемся в том же состоянии, ожидая новый выбор
    elif query.data == "signup_no":
        await query.edit_message_text(text="Жаль, но если передумаешь, я всегда тут! 😉 Хорошего дня!")
        return ConversationHandler.END

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает имя пользователя и запрашивает номер телефона."""
    user_name = update.message.text
    context.user_data['name'] = user_name
    logger.info(f"Имя пользователя: {user_name}")
    await update.message.reply_text(
        f"Приятно познакомиться, {user_name}! Теперь скажи, пожалуйста, твой номер телефона, "
        f"чтобы мы могли связаться с тобой и подтвердить запись."
    )
    return GET_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получает номер телефона и запрашивает подтверждение."""
    user_phone = update.message.text
    context.user_data['phone'] = user_phone
    logger.info(f"Телефон пользователя: {user_phone}")

    keyboard = [
        [InlineKeyboardButton("Да, всё верно", callback_data="phone_confirm_yes")],
        [InlineKeyboardButton("Нет, исправить", callback_data="phone_confirm_no")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Спасибо! Номер записан: {user_phone}. Всё верно?",
        reply_markup=reply_markup,
    )
    return CONFIRM_PHONE

async def confirm_phone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает подтверждение номера телефона."""
    query = update.callback_query
    await query.answer()

    if query.data == "phone_confirm_yes":
        keyboard = [
            [InlineKeyboardButton("Пятница, 18:00", callback_data="slot_friday")],
            [InlineKeyboardButton("Суббота, 15:00", callback_data="slot_saturday")],
            [InlineKeyboardButton("Воскресенье, 17:00", callback_data="slot_sunday")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="Теперь выбери, когда тебе удобно прийти на урок. Вот свободные слоты:",
            reply_markup=reply_markup,
        )
        return CHOOSE_SLOT
    elif query.data == "phone_confirm_no":
        await query.edit_message_text(text="Ой, давай исправим! Какой номер правильный?")
        return GET_PHONE # Возвращаемся к запросу номера

async def choose_slot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор слота времени."""
    query = update.callback_query
    await query.answer()

    user_choice = query.data
    user_name = context.user_data.get('name', 'Гость')
    user_phone = context.user_data.get('phone', 'Не указан')

    slot_text = ""
    if user_choice == "slot_friday":
        slot_text = "Пятница, 18:00"
    elif user_choice == "slot_saturday":
        slot_text = "Суббота, 15:00"
    elif user_choice == "slot_sunday":
        slot_text = "Воскресенье, 17:00"

    context.user_data['slot'] = slot_text
    logger.info(f"Пользователь {user_name} выбрал слот: {slot_text}")

    await query.edit_message_text(
        f"Отлично, {slot_text}! Записываю тебя, {user_name}, на бесплатный урок танго.\\n\\n"
        f"Всё готово! 📌 Ты записана на {slot_text}. "
        f'Адрес: ул. Танцевальная, 10 (студия \"ТангоМания\"). '
        f"Приходи в удобной одежде и с хорошим настроением! "
        f"Мы пришлём тебе напоминание на {user_phone} за день до урока. "
        f"Если что-то изменится, просто напиши мне (/cancel)"
    )
    return CONFIRMATION

async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ответ пользователя на финальном шаге."""
    user_response = update.message.text.lower()
    if "понятно" in user_response or "нет" in user_response:
        await update.message.reply_text("Супер, до встречи на танцполе! 💃🕺")
        return ConversationHandler.END
    elif "что брать" in user_response or "одежд" in user_response or "обув" in user_response:
        await update.message.reply_text(
            "Возьми удобную обувь (без каблука или на низком устойчивом каблуке, если привыкла) "
            "и одежду, в которой комфортно двигаться. Всё остальное — за нами! Ещё вопросы?"
        )
        return CONFIRMATION # Остаемся в этом же состоянии
    else:
        await update.message.reply_text(
            "Хм, я не совсем понял(а) вопрос. Если хочешь отменить запись, используй /cancel. "
            "Если вопросов нет, скоро увидимся!"
        )
        return CONFIRMATION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущий разговор."""
    user = update.message.from_user
    logger.info(f"Пользователь {user.first_name} отменил разговор.")
    await update.message.reply_text(
        "Запись отменена. Если передумаешь, просто напиши /start снова!",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear() # Очищаем данные пользователя при отмене
    return ConversationHandler.END

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для сообщений, которые не распознаны в рамках диалога."""
    await update.message.reply_text(
        "Ой, я не совсем понимаю. Пожалуйста, используй кнопки или отвечай на мои вопросы. "
        "Чтобы начать заново или отменить запись, используй /start или /cancel."
    )

def main() -> None:
    """Запускает бота."""
    if not BOT_TOKEN:
        logger.error("Токен бота не найден в .env файле!")
        return

    # Создание Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Создание ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_CHOICE: [
                CallbackQueryHandler(start_choice_callback, pattern="^(signup_yes|details|signup_no)$")
            ],
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CONFIRM_PHONE: [
                CallbackQueryHandler(confirm_phone_callback, pattern="^phone_confirm_(yes|no)$")
            ],
            CHOOSE_SLOT: [
                 CallbackQueryHandler(choose_slot_callback, pattern="^slot_(friday|saturday|sunday)$")
            ],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.TEXT & ~filters.COMMAND, fallback) # Обработчик для любых других текстовых сообщений
            ],
        # per_user=True чтобы хранить состояние для каждого пользователя отдельно
        # per_chat=True гарантирует, что состояние хранится для чата
        conversation_timeout=300 # Завершить диалог, если пользователь не отвечает 5 минут
    )

    application.add_handler(conv_handler)

    # Добавляем обработчик неизвестных команд, чтобы пользователь знал, что делать
    application.add_handler(MessageHandler(filters.COMMAND, fallback))

    # Запуск бота
    logger.info("Запуск бота...")
    application.run_polling()

if __name__ == "__main__":
    main() 