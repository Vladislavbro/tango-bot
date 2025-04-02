import logging
import os
from dotenv import load_dotenv
from logging import FileHandler

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

# --- Настройка логирования --- 

# 1. Создаем директорию для логов, если её нет
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 2. Настраиваем базовый логгер (для вывода в консоль)
log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Устанавливаем уровень для корневого логгера

# Убираем стандартные обработчики, чтобы избежать дублирования
if logger.hasHandlers():
    logger.handlers.clear()

# 3. Обработчик для вывода в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# 4. Обработчик для записи в файл
log_file_path = os.path.join(LOG_DIR, "tango_bot.log")
file_handler = FileHandler(log_file_path, encoding='utf-8') # Указываем кодировку
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# --- Конец настройки логирования --- 

# Определяем состояния разговора
START_CHOICE, GET_NAME, GET_PHONE, CONFIRM_PHONE, CHOOSE_SLOT, POST_CONFIRMATION = range(6)

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
    logger.info(f"Callback data received: {query.data}") # <-- Лог 1

    try:
        if query.data == "signup_yes":
            logger.info("Processing 'signup_yes'") # <-- Лог 2
            await query.edit_message_text(text="Отлично, давай запишем тебя! Как тебя зовут?")
            logger.info("Message edited for 'signup_yes', returning GET_NAME") # <-- Лог 3
            return GET_NAME
        elif query.data == "details":
            logger.info("Processing 'details'") # <-- Лог 4
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
            logger.info("Message edited for 'details', returning START_CHOICE") # <-- Лог 5
            return START_CHOICE # Остаемся в том же состоянии, ожидая новый выбор
        elif query.data == "signup_no":
            logger.info("Processing 'signup_no'") # <-- Лог 6
            await query.edit_message_text(text="Жаль, но если передумаешь, я всегда тут! 😉 Хорошего дня!")
            logger.info("Message edited for 'signup_no', returning END") # <-- Лог 7
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in start_choice_callback: {e}", exc_info=True) # <-- Лог ошибки
        # Можно добавить ответ пользователю об ошибке, если нужно
        # await query.message.reply_text("Произошла ошибка, попробуйте позже.")
        return ConversationHandler.END # Завершаем диалог в случае ошибки

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

    # Формируем и отправляем улучшенное сообщение с экранированием символов для MarkdownV2
    confirmation_message = (
        f"Отлично, {user_name}\\! 👍 Записываю тебя на бесплатный урок танго в {slot_text}\\.\n\n"
        f"📌 **Подтверждение записи:**\n"
        f"\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\- \n"
        f"**Слот:** {slot_text}\n"
        f"**Имя:** {user_name}\n"
        f"**Телефон:** {user_phone}\n"
        f'**Адрес:** ул\\. Танцевальная, 10 \\(студия \"ТангоМания\"\\)\n'
        f"\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\-\\- \n\n"
        f"Приходи в удобной одежде и с хорошим настроением\\! Мы пришлём напоминание за день до урока\\.\n\n"
        f"Если что\\-то изменится, напиши /cancel\\.\n"
    )

    await query.edit_message_text(
        text=confirmation_message,
        parse_mode='MarkdownV2' # Используем Markdown для форматирования
    )
    return POST_CONFIRMATION # Сразу переходим в состояние после подтверждения

async def post_confirmation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает сообщения пользователя после подтверждения записи."""
    slot_text = context.user_data.get('slot')
    if slot_text:
        # Экранируем символы для MarkdownV2
        slot_text_escaped = slot_text.replace("-", "\\-").replace(".", "\\.").replace("(", "\\(").replace(")", "\\)")
        user_name = context.user_data.get('name', 'Вы')
        user_name_escaped = user_name.replace("-", "\\-").replace(".", "\\.").replace("(", "\\(").replace(")", "\\)")

        await update.message.reply_text(
            f"{user_name_escaped}, вы уже записаны на {slot_text_escaped}\\. "
            f"Если хотите отменить запись, используйте /cancel\\.",
            parse_mode='MarkdownV2'
        )
    else:
        # Этого не должно произойти, но на всякий случай
        await update.message.reply_text(
            "Кажется, что\\-то пошло не так\\. Пожалуйста, начните сначала с команды /start\\.",
            parse_mode='MarkdownV2'
        )
    return POST_CONFIRMATION # Остаемся в этом состоянии

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
            POST_CONFIRMATION: [MessageHandler(filters.ALL & ~filters.Command('cancel') & ~filters.Command('start'), post_confirmation_handler)],
        },
        fallbacks=[
            CommandHandler("start", start), # Позволяем /start перезапустить диалог из любого места
            CommandHandler("cancel", cancel),
            MessageHandler(filters.COMMAND, fallback), # Обработчик для любых других команд внутри диалога
            MessageHandler(filters.TEXT & ~filters.COMMAND, fallback), # Обработчик для любых других текстовых сообщений
            MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.TEXT, fallback) # Обработчик для других типов сообщений
            ],
        # per_user=True чтобы хранить состояние для каждого пользователя отдельно
        # per_chat=True гарантирует, что состояние хранится для чата
        conversation_timeout=300 # Завершить диалог, если пользователь не отвечает 5 минут
    )

    application.add_handler(conv_handler)

    # Добавляем обработчик неизвестных команд, чтобы пользователь знал, что делать
    application.add_handler(MessageHandler(filters.COMMAND, fallback))

    # Добавляем обработчик для любого текста вне диалога, чтобы перезапускать его
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    # Запуск бота
    logger.info("Запуск бота...")
    application.run_polling()

if __name__ == "__main__":
    main() 